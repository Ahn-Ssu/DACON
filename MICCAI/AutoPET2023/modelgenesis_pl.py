from typing import Any, Optional
import numpy as np
from pytorch_lightning.utilities.types import STEP_OUTPUT

import torch
import torch.nn as nn
import torch.optim as optim 
import torch.nn.functional as F

from cosine_annealing_warmup import CosineAnnealingWarmupRestarts
from adamp import AdamP

import pytorch_lightning as pl
import pytorch_lightning.loggers as pl_loggers

from modelgenesis_utils import get_pair
from monai.losses.ssim_loss import SSIMLoss


class Modelgenesis_network(pl.LightningModule):
    def __init__(self, network, args) -> None:
        super().__init__()
        self.save_hyperparameters(ignore=['network'])
        
        self.model = network
        self.args = args
        self.loss = nn.MSELoss()
        self.modality = args.genesis_args.modality
        # self.loss = SSIMLoss() # Since the author said MSELoss is enough
        self.loss_log = []
        
    
    def configure_optimizers(self) -> Any:
        optimizer = AdamP(params=self.parameters(), lr=self.args.init_lr, betas=[0.9, 0.999], weight_decay=self.args.weight_decay)
        scheduler = CosineAnnealingWarmupRestarts(optimizer=optimizer, first_cycle_steps=self.args.epoch, max_lr=self.args.init_lr, min_lr=self.args.init_lr*self.args.lr_dec_rate, warmup_steps=self.args.epoch//20, gamma=0.8)
        return [optimizer], [scheduler]
    
    def training_step(self, batch, **kwargs: Any) -> STEP_OUTPUT:
        
        if self.modality == 'PET':
            y = batch['origin']
            x = batch['img']
        else:
            x, y = get_pair(img=batch['img'], batch_size=self.args.batch_size,
                        config=self.args.genesis_args)
        
        y_hat = self.model(x)
        loss = self.loss(y_hat, y)
        self.log("train_loss", loss.item(), on_step=False, on_epoch=True, prog_bar=True, logger=True, batch_size=self.args.batch_size, sync_dist=True)
        return loss
    
    def validation_step(self, batch, batch_idx) -> STEP_OUTPUT | None:
        self._shared_eval_step(batch, batch_idx)

    def on_validation_epoch_end(self) -> None:
        val_loss = np.mean(self.loss_log)

        self.log_dict({'val_loss':val_loss},
                       prog_bar=True, sync_dist=True)
        
        self.loss_log.clear()
    
    def _shared_eval_step(self, batch, batch_idx):
        if self.modality == 'PET':
            y = batch['origin']
            x = batch['img']
        else:
            x, y = get_pair(img=batch['img'], batch_size=self.args.batch_size,
                        config=self.args.genesis_args)
            
        y_hat = self.model(x)
        loss = self.loss(y_hat, y)
        self.loss_log.append(loss.item())
        
        # if self.current_epoch % 10 == 0:
        self.log_img_on_TB(x, y, y_hat, batch_idx)
        

    def log_img_on_TB(self, x, y, y_hat, batch_idx) -> None:
         
        # Get tensorboard logger
        tb_logger = None
        for logger in self.trainer.loggers:
            if isinstance(logger, pl_loggers.TensorBoardLogger):
                tb_logger = logger.experiment
                break

        if tb_logger is None:
                raise ValueError('TensorBoard Logger not found')
       
        target_idx = 64
        
        # tag, img_tensor, global_step=None#
        # add_images('title', data', dataformats='NCHW)
        tb_logger.add_image(tag=f"input/BZ[{batch_idx}]_{target_idx}",
                            img_tensor= x[..., target_idx, :],
                            global_step=self.current_epoch, 
                            dataformats='NCHW')
        tb_logger.add_image(tag=f"GT/BZ[{batch_idx}]_{target_idx}",
                            img_tensor= y[..., target_idx, :],
                            global_step=self.current_epoch, 
                            dataformats='NCHW')
        # tb_logger.add_image(f"PET_input/BZ[{batch_idx}]_{target_idx}", pet[..., target_idx, :], dataformats='CHW')
        tb_logger.add_image(tag=f"pred/BZ[{batch_idx}]_{target_idx}",
                            img_tensor= y_hat[..., target_idx, :],
                            global_step=self.current_epoch, 
                            dataformats='NCHW')
