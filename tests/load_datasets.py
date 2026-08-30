from datasets import load_dataset

ds = load_dataset('jacob-hugging-face/job-descriptions', split='train')
ds.to_csv('data/jd/hf_job_descriptions.csv')
