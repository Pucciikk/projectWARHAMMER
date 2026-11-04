package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.warpbound.gun.GunItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/** Точки входа для миксинов: сами миксины не должны знать ничего, кроме этого класса. */
public final class GunMixinHooks {
    private GunMixinHooks() {
    }

    public static boolean renderHand(AbstractClientPlayer player, float partialTick, InteractionHand hand, ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light) {
        // в кабине дредноута рук с оружием нет
        if (player.getVehicle() instanceof dev.warpbound.entity.dreadnought.concept.DreadConceptEntity) return true;
        // оружие занимает обе руки: вторую руку не рисуем, даже если в ней что-то лежит
        if (player.getMainHandItem().getItem() instanceof GunItem) {
            if (hand == InteractionHand.MAIN_HAND) GunView.render(player, partialTick, stack, pose, buffers, light);
            return true;
        }
        if (hand == InteractionHand.MAIN_HAND && stack.getItem() instanceof dev.warpbound.gear.ChainswordItem) {
            ChainswordView.render(player, partialTick, stack, pose, buffers, light);
            return true;
        }
        return false;
    }

    public static boolean hideCrosshair() {
        Minecraft mc = Minecraft.getInstance();
        if (inCockpit(mc)) return true;
        return mc.player != null && mc.player.getMainHandItem().getItem() instanceof GunItem && mc.options.getCameraType().isFirstPerson();
    }

    private static boolean inCockpit(Minecraft mc) {
        return mc.player != null && mc.player.getVehicle() instanceof dev.warpbound.entity.dreadnought.concept.DreadConceptEntity && mc.options.getCameraType().isFirstPerson();
    }

    public static float fovScale() {
        // смотровая щель: обзор уже обычного
        if (inCockpit(Minecraft.getInstance())) return 0.62f;
        GunItem gun = GunClient.held();
        if (gun == null || GunClient.aim < 0.001f) return 1f;
        float k = GunClient.aim * GunClient.aim * (3 - 2 * GunClient.aim);
        return 1 - (1 - GunVisual.of(gun).fovAim()) * k;
    }
}
