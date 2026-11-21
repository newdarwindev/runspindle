use runspindle_host::lifecycle::{
    Action, Adapter, Binding, CancelReply, Capabilities, Error, Event, LaunchReply, Observation,
    Peer, Presence, Request, Snapshot, Verifier, VERSION,
};
use runspindle_host::storage::Sqlite;
use serde::Deserialize;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::{env, fs::OpenOptions, io};

#[derive(Deserialize)]
#[serde(tag = "operation", rename_all = "snake_case")]
enum Command {
    Submit {
        presence: Presence,
        reply: Option<Observation>,
    },
    Reconcile {
        observations: Vec<Observation>,
    },
    Event {
        event: Event,
    },
    Snapshot,
    Capabilities,
}

#[derive(Deserialize)]
struct Step {
    binding: Binding,
    now: u64,
    #[serde(flatten)]
    command: Command,
}

struct Grant {
    binding: Binding,
    action: Option<Action>,
}
impl Verifier for Grant {
    fn verify(&self, candidate: &Binding, action: Action) -> bool {
        self.binding == *candidate && self.action == Some(action)
    }
}

struct ScriptedPeer {
    ledger: PathBuf,
    launch: Option<Observation>,
    discovery: Vec<Observation>,
}

impl ScriptedPeer {
    fn record(&self, entry: Value) {
        let mut stream = OpenOptions::new()
            .append(true)
            .open(&self.ledger)
            .expect("open fixture ledger");
        serde_json::to_writer(&mut stream, &entry).expect("write fixture ledger");
        std::io::Write::write_all(&mut stream, b"\n").expect("finish fixture ledger row");
    }
}

impl Peer for ScriptedPeer {
    fn launch(&mut self, binding: &Binding) -> LaunchReply {
        let observation = self.launch.take();
        self.record(json!({
            "call": "launch",
            "binding": binding,
            "effect": observation.as_ref().map(|value| &value.native_session_id),
        }));
        LaunchReply::Accepted(observation.expect("unexpected launch"))
    }

    fn discover(&mut self, binding: &Binding) -> Vec<Observation> {
        self.record(json!({"call": "discover", "binding": binding, "effect": null}));
        std::mem::take(&mut self.discovery)
    }

    fn cancel(&mut self, binding: &Binding, session_id: &str) -> CancelReply {
        self.record(json!({"call": "cancel", "binding": binding, "effect": session_id}));
        panic!("passive fixture forbids cancellation")
    }
}

fn output(result: Result<Snapshot, Error>) -> Value {
    match result {
        Ok(snapshot) => json!({"snapshot": snapshot}),
        Err(error) => json!({"error": format!("{error:?}")}),
    }
}

fn run(step: Step, store: &Path, ledger: PathBuf) -> Value {
    let action = match step.command {
        Command::Submit { .. } => Some(Action::Launch),
        Command::Reconcile { .. } => Some(Action::Reconcile),
        _ => None,
    };
    let mut host = Adapter::with_storage(
        Grant {
            binding: step.binding.clone(),
            action,
        },
        Sqlite::open(store).expect("open pinned Host store"),
        8,
        32,
        // Read the same explicit cutoff as the scenario. Adapter state also
        // rejects a changed cutoff when a later worker reopens the store.
        env::var("H09_MAX_AGE_MS")
            .expect("freshness window")
            .parse()
            .expect("integer freshness window"),
    )
    .expect("construct pinned Host adapter");
    let mut peer = ScriptedPeer {
        ledger,
        launch: None,
        discovery: Vec::new(),
    };
    match step.command {
        Command::Submit { presence, reply } => {
            peer.launch = reply;
            output(host.submit(
                Request {
                    version: VERSION.into(),
                    binding: step.binding,
                },
                &presence,
                step.now,
                &mut peer,
            ))
        }
        Command::Reconcile { observations } => {
            peer.discovery = observations;
            output(host.reconcile(&step.binding, step.now, &mut peer))
        }
        Command::Event { event } => output(host.event(&step.binding, event, step.now)),
        Command::Snapshot => output(host.snapshot(&step.binding)),
        Command::Capabilities => {
            let profile = |platform| {
                let capabilities = Capabilities::scripted(platform).expect("scripted profile");
                json!({
                    "platform": capabilities.platform,
                    "lifecycle": format!("{:?}", capabilities.lifecycle),
                    "capture": format!("{:?}", capabilities.capture),
                    "text_transfer": format!("{:?}", capabilities.text_transfer),
                    "submission": format!("{:?}", capabilities.submission),
                })
            };
            json!({"capabilities": [profile("linux"), profile("macos")]})
        }
    }
}

fn main() {
    let args: Vec<_> = env::args_os().skip(1).collect();
    let [store, ledger] = args.as_slice() else {
        panic!("expected temporary Host database and peer ledger");
    };
    let step = serde_json::from_reader(io::stdin().lock()).expect("synthetic fixture step");
    let report = run(step, Path::new(store), ledger.into());
    serde_json::to_writer(io::stdout().lock(), &report).expect("write worker report");
}
