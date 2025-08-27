import os 
import subprocess
import shutil 
from together import Together
from huggingface_hub import HfApi, create_repo

def upload_to_hf(ft_job_id: str, model_name, hf_username: str, cleanup = True, is_private = True):
    """
    model upload to hugginface. 

    Args:
        ft_job_id: id for fine-tuning job from together.ai
        model_name: name of model
        hf_username: huggingface username
        cleanup: delete model/files after upload 
    """
    client = Together(api_key = os.getenv('TOGETHER_API_KEY'))

    tar_filename = f"../models/{model_name}.tar.zst" # clean name for tar file; avoid "fellows-safety" prepend
    client.fine_tuning.download(id = ft_job_id, output = tar_filename, format = 'tar.zst') # download
    subprocess.run(['tar', '-xf', tar_filename]) # decompress

    hf_repo_name = f"{hf_username}/{model_name}" 
    api = HfApi(token = os.getenv('HF_TOKEN'))

    api.create_repo(repo_id = hf_repo_name, private = is_private, exist_ok = True)
    api.upload_folder(folder_path = tar_filename, repo_id = hf_repo_name) # folder path arg in this, line seems like it may not work (?) 

    # cleanup
    if cleanup:
        shutil.rmtree(f"../models/model_name")
        os.remove(tar_filename)
    # print(f"Model {model_name} uploaded to Hugging Face: https://huggingface.co/{hf_repo_name}")
    return f"https://huggingface.co/{hf_repo_name}"