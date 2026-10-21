package dev.warpbound.client.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import dev.warpbound.entity.multipart.HitboxPart;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.AABB;

public class DreadnoughtRenderer extends MobRenderer<DreadnoughtEntity, DreadnoughtModel> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Warpbound.id("dreadnought"), "main");
    private static final ResourceLocation TEXTURE = Warpbound.id("textures/entity/dreadnought.png");
    private static final RenderType GLOW = RenderType.eyes(Warpbound.id("textures/entity/dreadnought_glow.png"));

    public DreadnoughtRenderer(EntityRendererProvider.Context context) {
        super(context, new DreadnoughtModel(context.bakeLayer(LAYER)), 1.8f);
        // Линза, смотровая щель, решётка реактора светятся в темноте
        this.addLayer(new EyesLayer<>(this) {
            @Override
            public RenderType renderType() {
                return GLOW;
            }
        });
    }

    @Override
    public void render(DreadnoughtEntity entity, float yaw, float partialTick, PoseStack pose,
                       MultiBufferSource buffers, int light) {
        super.render(entity, yaw, partialTick, pose, buffers, light);
        // F3+B: ванилла рисует только общий габарит, части дорисовываем сами.
        // Красные — уязвимые места (саркофаг, голова, реактор)
        if (this.entityRenderDispatcher.shouldRenderHitBoxes() && !entity.isInvisible()) {
            double x = Mth.lerp(partialTick, entity.xOld, entity.getX());
            double y = Mth.lerp(partialTick, entity.yOld, entity.getY());
            double z = Mth.lerp(partialTick, entity.zOld, entity.getZ());
            var lines = buffers.getBuffer(RenderType.lines());
            for (HitboxPart part : entity.getHitboxParts()) {
                AABB box = part.getBoundingBox().move(-x, -y, -z);
                boolean weak = part.spec.armor() > 1.0f;
                LevelRenderer.renderLineBox(pose, lines, box, weak ? 1f : 0.3f, weak ? 0.2f : 1f, 0.2f, 1f);
            }
        }
    }

    @Override
    public ResourceLocation getTextureLocation(DreadnoughtEntity entity) {
        return TEXTURE;
    }

    @Override
    protected void scale(DreadnoughtEntity entity, PoseStack pose, float partialTick) {
        // Модель нарисована в 1/32 блока: вдвое детальнее текстура при том же размере
        pose.scale(0.5f, 0.5f, 0.5f);
    }

    @Override
    protected float getFlipDegrees(DreadnoughtEntity entity) {
        // Не заваливается на бок при смерти, как обычные мобы
        return 0f;
    }
}
