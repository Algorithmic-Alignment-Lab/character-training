from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
from pathlib import Path

import simple_parsing

from safetytooling.data_models.finetune import FinetuneConfig
from safetytooling.utils import utils
from together import Together

LOGGER = logging.getLogger(__name__)


async def upload_finetuning_file(
    client: Together,
    file_path: Path | None,
    check_delay: float = 1.0,
) -> str | None:
    """Upload file to Together and wait for processing."""
    if file_path is None:
        return None

    LOGGER.info(f"Uploading {file_path} to Together...")
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")
    if file_path.suffix != ".jsonl":
        raise ValueError(f"File {file_path} must have a .jsonl extension")
    response = client.files.upload(file=str(file_path))
    file_id = response.id
    LOGGER.info(f"Uploaded {file_path} to Together as {file_id}")

    while True:
        file_status = client.files.retrieve(file_id)
        if file_status.processed:
            return file_id

        LOGGER.info(f"Waiting for {file_id} to be processed...")
        await asyncio.sleep(check_delay)


async def main(cfg: TogetherFTConfig, verbose: bool = True):
    """Run Together fine-tuning job with monitoring."""
    # TODO: potentially add training data checking
    client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

    LOGGER.info("Uploading training and validation files...")
    train_file_id, val_file_id = await asyncio.gather(
        upload_finetuning_file(client, cfg.train_file),
        upload_finetuning_file(client, cfg.val_file),
    )
    assert train_file_id is not None

    LOGGER.info(f"Train file_id: {train_file_id}")
    LOGGER.info(f"Validation file_id: {val_file_id}")

    # Start fine-tuning job
    ft_job = client.fine_tuning.create(
        training_file=train_file_id,
        validation_file=val_file_id,
        model=cfg.model,
        n_epochs=cfg.n_epochs,
        n_checkpoints=cfg.n_evals,
        n_evals=cfg.n_evals,
        batch_size=cfg.batch_size,
        learning_rate=cfg.learning_rate,
        lora=cfg.lora,
        suffix=cfg.suffix,
        lora_r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        wandb_api_key=os.environ.get("WANDB_API_KEY"),
        wandb_project_name=cfg.wandb_project_name,
    )
    LOGGER.info(f"Started fine-tuning job: {ft_job.id}")

    LOGGER.info("Waiting for fine-tuning job to finish...")
    while True:
        status = client.fine_tuning.retrieve(ft_job.id)  # https://docs.together.ai/reference/get_fine-tunes-id
        if status.status == "completed":
            LOGGER.info("Fine-tuning job succeeded.")
            break
        elif status.status in ["error", "cancelled"]:
            LOGGER.error(f"Fine-tuning job failed: {status.status}")
            raise RuntimeError(f"Fine-tuning failed with status: {status.status}")

        await asyncio.sleep(10)

    LOGGER.info(f"Fine-tuning job finished with id <ft_id>{ft_job.id}</ft_id>")

    if cfg.save_folder is not None:
        assert status.output_name is not None, "Output name is None"
        output_name = status.output_name.replace("/", "|")

        if cfg.save_folder.endswith("/"):
            cfg.save_folder += f"{cfg.model}/{cfg.train_file.name.split('/')[-1].split('.')[0]}[id]{output_name}"
        else:
            cfg.save_folder += f"/{cfg.model}/{cfg.train_file.name.split('/')[-1].split('.')[0]}[id]{output_name}"

        os.makedirs(cfg.save_folder, exist_ok=True)
        if cfg.save_model:
            LOGGER.info("Saving model...")
            assert ft_job.id is not None
            save_model_path = cfg.save_folder + "/weights/model.tar.zst"
            client.fine_tuning.download(ft_job.id, output=save_model_path)
            LOGGER.info("Model saved.")
        if cfg.save_config:
            save_config_path = cfg.save_folder + "/train_config.json"
            ft_job_dict = ft_job.model_dump()
            ft_job_dict["lora_r"] = cfg.lora_r
            ft_job_dict["lora_alpha"] = cfg.lora_alpha
            ft_job_dict["lora_dropout"] = cfg.lora_dropout
            ft_job_dict["n_evals"] = cfg.n_evals
            with open(save_config_path, "w") as f:
                json.dump(ft_job_dict, f, indent=2)
            LOGGER.info("Config saved.")

    return ft_job


@dataclasses.dataclass
class TogetherFTConfig(FinetuneConfig):
    learning_rate: float = 1e-5
    n_evals: int = 1  # The number of evaluations to run and checkpoints to save.
    lora: bool = False
    lora_r: int = 8
    lora_alpha: int = 8
    lora_dropout: float = 0.0
    suffix: str = ""  # Together suffix to append to the model name

    save_model: bool = False


# Relevant Docs
# https://docs.together.ai/docs/fine-tuning-data-preparation#text-data
# https://docs.together.ai/docs/fine-tuning-models
if __name__ == "__main__":
    parser = simple_parsing.ArgumentParser()
    parser.add_arguments(TogetherFTConfig, dest="experiment_config")
    args = parser.parse_args()
    cfg: TogetherFTConfig = args.experiment_config
    print(cfg)
    utils.setup_environment(
        logging_level=cfg.logging_level,
    )

    asyncio.run(main(cfg))
