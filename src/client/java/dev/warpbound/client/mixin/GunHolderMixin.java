package dev.warpbound.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.warpbound.client.gun.GunRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.layers.ItemInHandLayer;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Рендер предмета не знает, кто его держит, а дуло нужно привязать к стрелку. */
@Mixin(ItemInHandLayer.class)
public abstract class GunHolderMixin {
    @Inject(method = "renderArmWithItem", at = @At("HEAD"))
    private void warpbound$begin(LivingEntity entity, ItemStack stack, ItemDisplayContext context, HumanoidArm arm, PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        GunRenderer.setHolder(entity);
    }

    @Inject(method = "renderArmWithItem", at = @At("RETURN"))
    private void warpbound$end(LivingEntity entity, ItemStack stack, ItemDisplayContext context, HumanoidArm arm, PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        GunRenderer.setHolder(null);
    }
}
