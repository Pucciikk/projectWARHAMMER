package dev.warpbound.client.mixin;

import dev.warpbound.client.gun.GunMixinHooks;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import com.mojang.blaze3d.vertex.PoseStack;

/** Оружие в руке рисуем сами: ванильная рука с предметом не умеет ни двух рук, ни прицеливания. */
@Mixin(ItemInHandRenderer.class)
public abstract class GunRenderMixins {
    @Inject(method = "renderArmWithItem", at = @At("HEAD"), cancellable = true)
    private void warpbound$gun(AbstractClientPlayer player, float partialTick, float pitch, InteractionHand hand, float swing, ItemStack stack, float equip,
                               PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        if (GunMixinHooks.renderHand(player, partialTick, hand, stack, pose, buffers, light)) ci.cancel();
    }
}
