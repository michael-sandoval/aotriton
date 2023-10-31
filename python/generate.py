import rules
import io
import shutil
import argparse
from pathlib import Path

SOURCE_PATH = Path(__file__).resolve()
COMPILER = SOURCE_PATH.parent / 'compile.py'

def parse():
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--target", type=str, default=None, help="Ahead of Time (AOT) Compile Architecture. PyTorch is required for autodetection if --target is missing.")
    args = p.parse_args()
    # print(args)
    return args

def gen_from_object(args, o : 'ObjectFileDescription', makefile):
    target = o._hsaco_kernel_path.name
    print(target, ':', file=makefile)
    cmd  = f'{COMPILER} {o.src.absolute()} --kernel_name {o.entrance} -o {o.obj.absolute()}'
    cmd += f' -g 1,1,1 --num_warps {o.num_warps} --num_stages {o.num_stages}'
    if args.target is not None:
        cmd += f" --target '{args.target}'"
    cmd += f" --signature '{o.signature}'"
    print('\t', cmd, '\n', file=makefile)
    return target

def gen_from_kernel(args, k, p, makefile):
    target_all = f'compile_{k.SHIM_KERNEL_NAME}'
    all_targets = []
    object_rules = io.StringIO()
    for o in k.get_object_files(p, prefix=k.SHIM_KERNEL_NAME):
        all_targets.append(gen_from_object(args, o, object_rules))
    print(target_all, ': ', end='', file=makefile)
    for t in all_targets:
        print(t, end=' ', file=makefile)
    print('\n\n', file=makefile)
    object_rules.seek(0)
    shutil.copyfileobj(object_rules, makefile)
    return target_all

def main():
    args = parse()
    build_dir = Path('build/')
    with open(build_dir / 'Makefile.compile', 'w') as f:
        makefile_content = io.StringIO()
        per_kernel_targets = []
        for k in rules.kernels:
            per_kernel_targets.append(gen_from_kernel(args, k, build_dir, makefile_content))
        print('all: ', end='', file=f)
        for t in per_kernel_targets:
            print(t, end=' ', file=f)
        print('\n', file=f)
        makefile_content.seek(0)
        shutil.copyfileobj(makefile_content, f)
        print('.PHONY: all ', ' '.join(per_kernel_targets), file=f)

if __name__ == '__main__':
    main()
