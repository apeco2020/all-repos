import argparse
import contextlib
import os
import sys
import tempfile

from all_repos import autofix_lib
from all_repos import cli
from all_repos.config import load_config
from all_repos.grep import repos_matching


@contextlib.contextmanager
def tmp_pre_commit_home(*, _absent=object()):
    """During lots of autoupdates, many repositories will be cloned into the
    pre-commit directory.  This prevents leaving many MB/GB of repositories
    behind due to this autofixer.  This context creates a temporary directory
    so these many repositories are automatically cleaned up.
    """
    before = os.environ.get('PRE_COMMIT_HOME', _absent)
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['PRE_COMMIT_HOME'] = tmpdir
        try:
            yield
        finally:
            if before is _absent:
                os.environ.pop('PRE_COMMIT_HOME', None)
            else:
                os.environ['PRE_COMMIT_HOME'] = before


def _run_all_files(**kwargs):
    autofix_lib.run(
        sys.executable, '-m', 'pre_commit', 'run', '--all-files', **kwargs,
    )


def apply_fix():
    autofix_lib.run(sys.executable, '-m', 'pre_commit', 'autoupdate')
    # This may return nonzero for fixes, that's ok!
    _run_all_files(check=False)


def check_fix():
    _run_all_files()


def main(argv=None):
    parser = argparse.ArgumentParser()
    cli.add_fixer_args(parser)
    args = parser.parse_args()

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    assert args.jobs == 1, 'https://github.com/pre-commit/pre-commit/issues/363'  # noqa

    config = load_config(args.config_filename)
    repos = repos_matching(config, ('', '--', '.pre-commit-config.yaml'))

    repos, commit, autofix_settings = autofix_lib.from_cli(
        args,
        repos=repos,
        msg='Ran pre-commit autoupdate.', branch_name='pre-commit-autoupdate',
    )

    with tmp_pre_commit_home():
        autofix_lib.fix(
            repos,
            apply_fix=apply_fix,
            check_fix=check_fix,
            config=config,
            commit=commit,
            autofix_settings=autofix_settings,
        )


if __name__ == '__main__':
    exit(main())