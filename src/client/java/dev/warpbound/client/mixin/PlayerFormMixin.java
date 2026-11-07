package dev.warpbound.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.warpbound.client.player.ClientGeneForms;
import dev.warpbound.client.player.PlayerFormRenderer;
import dev.warpbound.player.GeneForm;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.EnumMap;
import java.util.Map;

/**
 * Игрок после генной модификации рисуется моделью своей формы (Астартес, Громовой воин) вместо ванильной.
 * Рендеры форм создаются вместе с ванильным (тот же контекст, пересоздаются при перезагрузке ресурсов).
 */
@Mixin(PlayerRenderer.class)
public abstract class PlayerFormMixin {
    @Unique
    private final Map<GeneForm, PlayerFormRenderer> warpbound$forms = new EnumMap<>(GeneForm.class);

    @Inject(method = "<init>", at = @At("TAIL"))
    private void warpbound$createForms(EntityRendererProvider.Context context, boolean slim, CallbackInfo ci) {
        for (GeneForm f : GeneForm.values()) if (f.model() != null) warpbound$forms.put(f, new PlayerFormRenderer(context, f));
    }

    @Inject(method = "render(Lnet/minecraft/client/player/AbstractClientPlayer;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V",
            at = @At("HEAD"), cancellable = true)
    private void warpbound$renderForm(AbstractClientPlayer player, float yaw, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int light, CallbackInfo ci) {
        PlayerFormRenderer r = warpbound$forms.get(ClientGeneForms.get(player));
        if (r == null) return;
        r.render(player, yaw, partialTick, poseStack, buffers, light);
        ci.cancel();
    }

    /** От первого лица пустая рука — латная перчатка формы. */
    @Inject(method = "renderRightHand", at = @At("HEAD"), cancellable = true)
    private void warpbound$rightHand(PoseStack poseStack, MultiBufferSource buffers, int light, AbstractClientPlayer player, CallbackInfo ci) {
        warpbound$hand(poseStack, buffers, light, player, true, ci);
    }

    @Inject(method = "renderLeftHand", at = @At("HEAD"), cancellable = true)
    private void warpbound$leftHand(PoseStack poseStack, MultiBufferSource buffers, int light, AbstractClientPlayer player, CallbackInfo ci) {
        warpbound$hand(poseStack, buffers, light, player, false, ci);
    }

    @Unique
    private void warpbound$hand(PoseStack poseStack, MultiBufferSource buffers, int light, AbstractClientPlayer player, boolean right, CallbackInfo ci) {
        PlayerFormRenderer r = warpbound$forms.get(ClientGeneForms.get(player));
        if (r == null) return;
        r.renderFirstPersonArm(poseStack, buffers, light, player, right);
        ci.cancel();
    }
}
