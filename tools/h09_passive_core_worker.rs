use runspindle_core::browser_control::{
    self, PassiveAuthority, RetainedControlState, Transition, TransitionData,
};
use runspindle_core::browser_effect_registry::BrowserRegistry;
use runspindle_core::browser_effect_wire::{Action, Peer, Target, EVIDENCE_CLASS, VERSION};
use runspindle_core::durable::digest;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{env, fs::OpenOptions, io, io::Write, path::PathBuf};

#[derive(Deserialize)]
struct Request {
    action: String,
    selection: Target,
    grant: Option<Target>,
}

struct SetupGrant(Transition);
impl browser_control::Authority for SetupGrant {
    fn allow_schema_upgrade(&self) -> bool {
        true
    }
    fn verify(&self, transition: &Transition, _: Action) -> bool {
        self.0 == *transition
    }
    fn initialize_proven(&self, transition: &Transition) -> bool {
        self.0 == *transition
    }
}

struct ReadGrant(Option<Target>);
impl PassiveAuthority for ReadGrant {
    fn verify(&self, selection: &Target) -> bool {
        self.0.as_ref() == Some(selection)
    }
}

struct ScriptedFence(PathBuf);
impl Peer for ScriptedFence {
    fn exchange(&mut self, request: &[u8]) -> anyhow::Result<Vec<u8>> {
        let request_value: Value = serde_json::from_slice(request)?;
        let action = request_value["action"].as_str().unwrap();
        anyhow::ensure!(matches!(action, "dispatch" | "reconcile"));
        let mut file = OpenOptions::new().append(true).open(&self.0)?;
        serde_json::to_writer(
            &mut file,
            &json!({"action": action, "target": request_value["target"]}),
        )?;
        file.write_all(b"\n")?;
        Ok(serde_json::to_vec(&json!({
            "version": VERSION, "request_sha256": digest(request),
            "evidence_class": EVIDENCE_CLASS, "outcome": "confirmed",
        }))?)
    }
}

fn run(request: Request, db: PathBuf, ledger: PathBuf) -> anyhow::Result<Value> {
    let mut registry = BrowserRegistry::open(db)?;
    if request.action == "status" {
        let status = registry.passive_control_status(&request.selection, &ReadGrant(request.grant));
        return Ok(match status {
            Ok(report) => {
                let head = report.head.map(|head| {
                    let (phase, holder) = match head.state {
                        RetainedControlState::Pending => ("pending", None),
                        RetainedControlState::Confirmed(holder) => ("confirmed", Some(holder)),
                        RetainedControlState::Rejected => ("rejected", None),
                        RetainedControlState::Conflict => ("conflict", None),
                    };
                    json!({"epoch": head.epoch, "generation": head.generation, "phase": phase, "holder": holder})
                });
                json!({"selection": report.selection, "head": head})
            }
            Err(_) => json!({"status": "denied"}),
        });
    }

    let mut target = request.selection;
    target.binding.intent = browser_control::intent(&target)?;
    target.binding.revision = 1;
    target.binding.epoch = 1;
    target.binding.operation = "fixture-initialize".into();
    let transition = Transition {
        target,
        data: TransitionData {
            version: browser_control::DOMAIN.into(),
            action: browser_control::TransferKind::Initialize,
            source: None,
            destination: browser_control::Holder {
                kind: browser_control::HolderKind::Agent,
                identity: "fixture-agent".into(),
            },
            predecessor: None,
        },
    };
    let setup = SetupGrant(transition.clone());
    let mut fence = ScriptedFence(ledger);
    match request.action.as_str() {
        "seed" => {
            registry.upgrade_control_schema(&setup)?;
            registry.dispatch_control(&transition, &setup, &mut fence)?;
        }
        "confirm" => {
            registry.reconcile_control(&transition, &setup, &mut fence)?;
        }
        _ => anyhow::bail!("unknown fixture action"),
    }
    Ok(json!({"setup_target": transition.target}))
}

fn main() -> anyhow::Result<()> {
    let args: Vec<_> = env::args_os().skip(1).map(PathBuf::from).collect();
    let [db, ledger] = args.as_slice() else {
        anyhow::bail!("expected fixture database and effect ledger");
    };
    let request = serde_json::from_reader(io::stdin().lock())?;
    serde_json::to_writer(
        io::stdout().lock(),
        &run(request, db.clone(), ledger.clone())?,
    )?;
    Ok(())
}
