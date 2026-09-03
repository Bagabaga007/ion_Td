"""ion-td 命令行。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import PredictionConfig, load_config
from .dataset import PENTAZOLATE_SMILES, load_training_records
from .geometry import optimize_cation
from .model import predict_temperature, validate_model


def _prediction_config(args: argparse.Namespace) -> PredictionConfig:
    if args.config:
        return load_config(args.config)
    if not args.name or not args.cation:
        raise ValueError("未使用 --config 时必须提供 --name 和 --cation")
    return PredictionConfig(
        name=args.name,
        cation_smiles=args.cation,
        anion_smiles=args.anion,
        allow_out_of_domain=args.allow_out_of_domain,
    )


def _cmd_predict(args: argparse.Namespace) -> int:
    config = _prediction_config(args)
    result = predict_temperature(
        config.cation_smiles,
        name=config.name,
        anion_smiles=config.anion_smiles,
        allow_out_of_domain=config.allow_out_of_domain or args.allow_out_of_domain,
    )
    payload = result.to_dict()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n")
    print(text)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    result = validate_model()
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


def _cmd_show_data(args: argparse.Namespace) -> int:
    records = load_training_records()
    print(f"records={len(records)}")
    print(f"temperature_range_c={min(r.tdec_c for r in records):.2f}..{max(r.tdec_c for r in records):.2f}")
    print(f"anion={PENTAZOLATE_SMILES}")
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    result = optimize_cation(
        args.cation,
        output_dir=args.output_dir,
        name=args.name,
        seed=args.seed,
        xtb_executable=args.xtb,
        timeout=args.timeout,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ion-td", description="五唑离子盐热分解温度实验性评估")
    sub = parser.add_subparsers(dest="command", required=True)

    predict = sub.add_parser("predict", help="预测并输出适用域/不确定性")
    predict.add_argument("--config")
    predict.add_argument("--name")
    predict.add_argument("--cation")
    predict.add_argument("--anion", default=PENTAZOLATE_SMILES)
    predict.add_argument("--allow-out-of-domain", action="store_true")
    predict.add_argument("--output")
    predict.set_defaults(func=_cmd_predict)

    validate = sub.add_parser("validate", help="重算严格留一法指标")
    validate.set_defaults(func=_cmd_validate)

    show = sub.add_parser("show-data", help="显示训练数据范围")
    show.set_defaults(func=_cmd_show_data)

    optimize = sub.add_parser("optimize", help="确定性生成阳离子结构并运行 xTB")
    optimize.add_argument("--name", required=True)
    optimize.add_argument("--cation", required=True)
    optimize.add_argument("--output-dir", required=True)
    optimize.add_argument("--seed", type=int, default=20260903)
    optimize.add_argument("--xtb")
    optimize.add_argument("--timeout", type=int, default=600)
    optimize.set_defaults(func=_cmd_optimize)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
