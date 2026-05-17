import argparse

from japan.runner import run_validation


def build_parser():
    parser = argparse.ArgumentParser(description="Japan KEGG validation runner")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--clean-run", action="store_true", help="Start a fresh run from the input workbook")
    mode_group.add_argument("--resume", action="store_true", help="Resume from the latest checkpoint")
    mode_group.add_argument("--resume-from", metavar="CHECKPOINT", help="Resume from a named or explicit checkpoint path")
    mode_group.add_argument("--resolve-errors", action="store_true", help="Retry only rows marked Error in the latest checkpoint")
    return parser


def parse_mode(args):
    if args.clean_run:
        return "clean-run", None
    if args.resume:
        return "resume", None
    if args.resume_from:
        return "resume-from", args.resume_from
    return "resolve-errors", None


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    mode, checkpoint_ref = parse_mode(args)
    summary = run_validation(mode=mode, checkpoint_ref=checkpoint_ref)
    print(
        "Completed {mode}: processed={processed}, all_match={all_match}, mismatched={mismatched}, "
        "not_found={not_found}, errors={errors}, output={output_file}".format(**summary)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
