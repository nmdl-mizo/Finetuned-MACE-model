import os
import argparse
import logging
import torch
from torch.utils.data import ConcatDataset
from ase.io import read
from equivar_eval.scripts.finetune_r import run_training
from sklearn.model_selection import train_test_split

def concat_data(xyz_list):
    datasets = []
    for xyz in xyz_list:
        structures = read(xyz, index = ":")
        datasets.extend(structures)
    return datasets


def main():
    parser = argparse.ArgumentParser(
        description="Finetune Equivar model with concatenated BEC datasets."
    )

    # Model & device
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to the pretrained Equivar model (.pt)."
    )
    parser.add_argument(
        "--cuda_mem_frac",
        type=float,
        default=1.0,
        help="CUDA memory fraction per process (default: 1)."
    )

    # Dataset lists
    parser.add_argument(
        "--train_xyz",
        type=str,
        nargs="+",
        required=True,
        help="List of training dataset .xyz files."
    )
    parser.add_argument(
        "--valid_ratio",
        type=float,
        default=0.2,
        help="Ratio of validation dataset"
    )
    parser.add_argument(
        "--test_xyz",
        type=str,
        nargs="+",
        default=None,
        help="List of test dataset .xyz files."
    )

    # Training hyperparameters
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Batch size (default: 4)."
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=300,
        help="Maximum number of training epochs (default: 300)."
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=20,
        help="Early stopping patience (default: 20)."
    )
    parser.add_argument(
        "--output_model",
        type=str,
        default="finetuned_bec_model.pth",
        help="Output model name."
    )
    parser.add_argument(
        "--random_state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    # Silence logging
    logging.getLogger("root").setLevel(logging.ERROR)

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.set_per_process_memory_fraction(args.cuda_mem_frac, device=0)

    # Load model
    model = torch.jit.load(args.model, map_location=device)
    model.eval()

    # Load datasets
    dataset = concat_data(args.train_xyz)
    train_dataset, valid_dataset = train_test_split(
        dataset,
        test_size=args.valid_ratio,
        random_state=args.random_state
    )
    if args.test_xyz is not None:
        test_dataset = concat_data(args.test_xyz)
    else:
        test_dataset = None

    print(f"train: {len(train_dataset)} data")
    print(f"valid: {len(valid_dataset)} data")
    if args.test_xyz is not None:
        print(f"test: {len(test_dataset)} data")
    else:
        print(f"test: 0 data")

    print("Start finetuning")
    run_training(
        model,
        train_dataset,
        valid_dataset,
        test_dataset,
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
        patience=args.patience,
        device=device,
        output_model_name=args.output_model,
    )
    print("Finish finetuning")


if __name__ == "__main__":
    main()
