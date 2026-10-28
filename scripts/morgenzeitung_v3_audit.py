"""Immutable private snapshots for reproducing actual reader-learning selection.

Must run in a checked out PRIVATE feedback repository, never in the public
Pages repository. Does not access publishers, infer ratings or mutate profiles.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from scripts.morgenzeitung_v3_engine import compare_learning, load_edition_history


def digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def engine_identity():
    root=Path(__file__).resolve().parent
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(root.glob("morgenzeitung_v3_*.py"))}
    try:
        commit=subprocess.run(["git","rev-parse","HEAD"],cwd=root,
                              check=True,capture_output=True,text=True).stdout.strip()
    except (OSError,subprocess.CalledProcessError):commit=None
    return {"commit":commit,"files":files}


def before_snapshot(pool, profile, date, history=(), selection=None):
    if not isinstance(pool, dict) or not all(isinstance(pool.get(k), list) for k in ("articles", "headlines")):
        raise ValueError("Original candidate file must contain articles and headlines arrays")
    if not isinstance(profile, dict):
        raise ValueError("Frozen profile required")
    if not isinstance(selection,dict) or set(selection)!={"articles","headlines"}:
        raise ValueError("Actual selection parameters required for both sections")
    for key,maximum in (("articles",15),("headlines",20)):
        options=selection[key]
        if (set(options)!={"limit","discovery_slots","min_score"}
            or type(options["limit"]) is not int or not 1<=options["limit"]<=maximum
            or type(options["discovery_slots"]) is not int or not 0<=options["discovery_slots"]<=options["limit"]
            or isinstance(options["min_score"],bool) or not isinstance(options["min_score"],(int,float))
            or not 0<=options["min_score"]<=50):
            raise ValueError("Invalid actual selection parameters")
    data={"version":2, "date":date,"selection":selection,"engine":engine_identity(),
          "frozen_profile":profile,
          "original_candidates":pool,
          "previous_editions":list(history),
          "source_hashes":{"profile":digest(profile), "candidates":digest(pool),
                           "previous_editions":digest(list(history))},
          "private_only":True, "ratings_fabricated":False}
    data["snapshot_sha256"]=digest({k:v for k,v in data.items() if k!="snapshot_sha256"})
    return json.loads(json.dumps(data))


def learning_result(snapshot, after):
    if digest({k:v for k,v in snapshot.items() if k!="snapshot_sha256"})!=snapshot.get("snapshot_sha256"):
        raise ValueError("Frozen pre-selection snapshot has changed")
    if digest(snapshot["frozen_profile"])!=snapshot["source_hashes"]["profile"]:
        raise ValueError("Frozen initial profile hash invalid")
    if digest(snapshot["original_candidates"])!=snapshot["source_hashes"]["candidates"]:
        raise ValueError("Original candidate pool hash invalid")
    if digest(snapshot["previous_editions"])!=snapshot["source_hashes"]["previous_editions"]:
        raise ValueError("Past-edition input hash invalid")
    if snapshot.get("version")!=2 or snapshot.get("engine",{}).get("files")!=engine_identity()["files"]:
        raise ValueError("Exact frozen engine required; do not replay with changed code")
    before=snapshot["frozen_profile"]
    pool=snapshot["original_candidates"]
    history=snapshot["previous_editions"]
    date=snapshot["date"]
    comparisons={}
    for key,section in (("articles","Vertiefungen"),("headlines","Heute wichtig")):
        comparisons[section]=compare_learning(
            pool[key],before,after,new_feedback=before.get("feedback_by_issue")!=after.get("feedback_by_issue"),
            section=section,**snapshot["selection"][key],
            previous_editions=history,edition_date=date if history else None)
    return {
        "date":date, "snapshot_sha256":snapshot["snapshot_sha256"],
        "before_profile_sha256":snapshot["source_hashes"]["profile"],
        "after_profile_sha256":digest(after),
        "comparison":comparisons,"selection":snapshot["selection"],"engine":snapshot["engine"], "private_only":True,
        "feedback_quality_improvement_proven":False,
        "note":"Genuine frozen input pool. Changed ranking does not prove better article quality.",
    }


def private_target(root, relative):
    """Reject public-repo output and unsafe paths, including symlinks."""
    base=Path(root).resolve()
    config=base/".git/config"
    if not config.is_file() or "morgenzeitung-feedback" not in config.read_text(encoding="utf-8"):
        raise ValueError("Output requires a checked-out private morgenzeitung-feedback repository")
    target=(base/relative).resolve()
    if not target.is_relative_to(base) or not target.is_relative_to(base/"morgenzeitung-v3"):
        raise ValueError("Snapshot must stay in private morgenzeitung-v3 directory")
    if target.suffix!=".json":
        raise ValueError("Private output must be JSON")
    return target


def read(path):
    with open(path,encoding="utf-8") as fp:
        return json.load(fp)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("before","after"))
    p.add_argument("--private-root",required=True)
    p.add_argument("--output",required=True,help="Relative private file, e.g. morgenzeitung-v3/snapshots/date-before.json")
    p.add_argument("--profile",required=True)
    p.add_argument("--candidates")
    p.add_argument("--date")
    p.add_argument("--history-dir",help="Optional exact previous edition index used to rank")
    p.add_argument("--snapshot")
    p.add_argument("--selection",help="JSON file with actual limit, discovery_slots, min_score for articles/headlines")
    args=p.parse_args()
    dest=private_target(args.private_root,args.output)
    if dest.exists():
        raise ValueError("Immutable snapshot/report already exists: "+str(dest))
    if args.action=="before":
        if not args.candidates or not args.date or not args.selection: p.error("before needs --candidates, --date and --selection")
        history=load_edition_history(args.history_dir) if args.history_dir else []
        result=before_snapshot(read(args.candidates),read(args.profile),args.date,history,read(args.selection))
    else:
        if not args.snapshot:p.error("after needs --snapshot")
        source=Path(args.snapshot).resolve()
        if not source.is_relative_to(Path(args.private_root).resolve()):
            raise ValueError("Read frozen before snapshot from the private repository")
        result=learning_result(read(source),read(args.profile))
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive create is atomic: a competing run must NEVER truncate an
    # earlier immutable private audit, even between exists() and write().
    try:
        with dest.open("x",encoding="utf-8") as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise ValueError("Immutable snapshot/report already exists: "+str(dest)) from exc
    print(json.dumps({"ok":True,"private_path":str(dest),"snapshot_sha256":result["snapshot_sha256"],
                      "quality_proven":result.get("feedback_quality_improvement_proven",False)},ensure_ascii=False))


if __name__=="__main__":
    main()
