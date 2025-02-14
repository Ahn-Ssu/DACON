# https://github.com/Lyken17/pytorch-OpCounter/blob/master/benchmark/evaluate_famous_models.py


import torch
import torchvision.models as models

from model import unet_baseline, late_fusion
from thop import profile

from monai.networks.nets import SwinUNETR


def model_size_info(model, input):
    flops, params = profile(model=model, inputs=(input,), verbose=False)
    print("%10s | %10s | %10s" % ("Model", "Params(M)", "FLOPs(G)"))
    print("-----------|------------|-----------")
    print(
            "%10s | %10.2f | %10.2f" % (model.__class__.__name__, params / (1000 ** 2), flops / (1000 ** 3))
        )
    print()
input = torch.rand(1, 2, 128, 128, 128)

model = late_fusion.UNet_lateF(
                            spatial_dim=3,
                            input_dim=2,
                            out_dim=2,
                            hidden_dims=[16,32,64,128,256], # 16 32 32 64 128 is default setting of Monai
                            dropout_p=0.,
                            use_MS=True
                        )

model_size_info(model, input)
model = SwinUNETR(
    img_size=128,
    in_channels=2,
    out_channels=2,
    depths=(2,2,2,2),
    feature_size=24,
    spatial_dims=3
)

model_size_info(model, input)






## 3x3x3 kernel UNet with 2 channel input dim and hidden_dims =[32,32,64,128,256]
#      Model |  Params(M) |   FLOPs(G)
# -----------|------------|-----------
#       UNet |       5.75 |     323.69

## 5x5x5 kernel UNet with 2 channel input dim and hidden_dims =[32,32,64,128,256]
#      Model |  Params(M) |   FLOPs(G)
# -----------|------------|-----------
#       UNet |      25.32 |    1403.91

## 7x7x7 kernel UNet with 2 channel input dim and hidden_dims =[32,32,64,128,256]
#      Model |  Params(M) |   FLOPs(G)
# -----------|------------|-----------
#       UNet |      68.87 |    3806.84







##########################
######## example #########
##########################
# input = torch.rand(1, 3, 224, 224)
# vgg16 = models.vgg16()
# flops, params = profile(model=vgg16, inputs=(input,), verbose=False)


# print("%10s | %10s | %10s" % ("Model", "Params(M)", "FLOPs(G)"))
# print("-----------|------------|-----------")
# print(
#         "%10s | %10.2f | %10.2f" % (vgg16.__class__.__name__, params / (1000 ** 2), flops / (1000 ** 3))
#     )
# print()
