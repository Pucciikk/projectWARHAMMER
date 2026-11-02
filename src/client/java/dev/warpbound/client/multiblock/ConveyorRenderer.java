package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.warpbound.industry.machine.ConveyorBlock;
import dev.warpbound.industry.machine.ConveyorBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.world.item.ItemDisplayContext;

/** Предметы на ленте лежат плашмя и плавно едут: положение считается между тиками. */
public final class ConveyorRenderer implements BlockEntityRenderer<ConveyorBlockEntity> {
    private static final float SPEED = 0.05f;

    @Override
    public void render(ConveyorBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        if (be.batches().isEmpty()) return;
        Direction facing = be.getBlockState().getValue(ConveyorBlock.FACING);
        var renderer = Minecraft.getInstance().getItemRenderer();
        float end = be.endAt();
        for (var b : be.batches()) {
            float at = Math.min(end, b.at + SPEED * partialTick);
            pose.pushPose();
            pose.translate(0.5 + facing.getStepX() * (at - 0.5), 0.5, 0.5 + facing.getStepZ() * (at - 0.5));
            pose.mulPose(Axis.YP.rotationDegrees(-facing.toYRot()));
            pose.mulPose(Axis.XP.rotationDegrees(62));   // чуть привстав: так предмет читается и с низкой камеры
            pose.scale(0.5f, 0.5f, 0.5f);
            renderer.renderStatic(b.stack, ItemDisplayContext.FIXED, light, OverlayTexture.NO_OVERLAY, pose, buffers, be.getLevel(), 0);
            pose.popPose();
        }
    }
}
