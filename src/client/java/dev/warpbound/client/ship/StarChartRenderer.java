package dev.warpbound.client.ship;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import dev.warpbound.Warpbound;
import dev.warpbound.ship.block.StarChartBlock;
import dev.warpbound.ship.block.StarChartBlockEntity;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;

/**
 * Табло карты Империума: светящийся квадрат 7×4 блока на стене позади блока карты.
 * Картинка та же, что на экране карты (tools/textures/gen_star_map.py); яркость чуть дышит, как у гололита.
 */
public class StarChartRenderer implements BlockEntityRenderer<StarChartBlockEntity> {
    public static final ResourceLocation MAP = Warpbound.id("textures/gui/star_map.png");
    /** Отступ табло от стены (в блоках): поверх тонкой плиты блока. */
    private static final float DEPTH = 2.2f / 16f;

    @Override
    public void render(StarChartBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        Direction facing = be.getBlockState().getValue(StarChartBlock.FACING);
        float time = (be.getLevel() == null ? 0 : be.getLevel().getGameTime()) + partialTick;
        int bright = 225 + (int) (20 * Math.sin(time * 0.05));

        pose.pushPose();
        pose.translate(0.5, 0, 0.5);
        pose.mulPose(Axis.YP.rotationDegrees(-facing.toYRot()));
        pose.translate(-0.5, 0, -0.5);
        // в этой системе зритель на +Z, стена на z = 0; влево-вправо — X
        float half = StarChartBlock.WIDTH / 2f;
        float x0 = 0.5f - half, x1 = 0.5f + half, y0 = 0, y1 = StarChartBlock.HEIGHT;
        VertexConsumer vc = buffers.getBuffer(RenderType.entityCutoutNoCull(MAP));
        PoseStack.Pose p = pose.last();
        vertex(vc, p, x0, y0, 0, 1, bright);
        vertex(vc, p, x1, y0, 1, 1, bright);
        vertex(vc, p, x1, y1, 1, 0, bright);
        vertex(vc, p, x0, y1, 0, 0, bright);
        pose.popPose();
    }

    private static void vertex(VertexConsumer vc, PoseStack.Pose p, float x, float y, float u, float v, int bright) {
        vc.addVertex(p, x, y, DEPTH).setColor(bright, bright, bright, 255).setUv(u, v)
                .setOverlay(OverlayTexture.NO_OVERLAY).setLight(LightTexture.FULL_BRIGHT).setNormal(p, 0, 0, 1);
    }

    @Override
    public boolean shouldRenderOffScreen(StarChartBlockEntity be) {
        return true;
    }
}
