import torch
import timm
from torchgeo.models import ResNet50_Weights

# Load TorchGeo pretrained backbone weights
weights = ResNet50_Weights.SENTINEL2_ALL_MOCO

# Create ResNet50 backbone (no classifier)
backbone = timm.create_model(
    "resnet50",
    in_chans=weights.meta["in_chans"],
    num_classes=0  # backbone only
)

# Load pretrained weights
backbone.load_state_dict(weights.get_state_dict(progress=True), strict=False)
backbone.eval()

# Simple classification head (10 land-use classes)
classifier = torch.nn.Linear(backbone.num_features, 10)

# Full model
model = torch.nn.Sequential(backbone, classifier)
model.eval()

# Dummy Sentinel-2 input
dummy_image = torch.randn(1, weights.meta["in_chans"], 224, 224)

with torch.no_grad():
    output = model(dummy_image)

print("Prediction shape:", output.shape)
