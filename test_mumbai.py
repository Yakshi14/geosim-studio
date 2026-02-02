from torchgeo.samplers import RandomGeoSampler
from torch.utils.data import DataLoader
from torchgeo.datasets.utils import stack_samples
from data.processed.mumbai_dataset import MumbaiTilesDataset

# Create dataset
dataset = MumbaiTilesDataset("data/processed/mumbai_tiles")

# Create sampler with explicit roi
sampler = RandomGeoSampler(dataset, size=256, length=5, roi=dataset.bounds)

# Create DataLoader
loader = DataLoader(dataset, batch_size=2, sampler=sampler, collate_fn=stack_samples)

# Get one batch
batch = next(iter(loader))
print("Image batch shape:", batch["image"].shape)
print("Bounding boxes:", batch["bbox"])
