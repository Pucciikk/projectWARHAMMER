package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.industry.machine.PortedMachine;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockHost;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.cache.object.GeoQuad;
import software.bernie.geckolib.cache.object.GeoVertex;
import software.bernie.geckolib.model.DefaultedBlockGeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

/**
 * Собранная машина: ядро рисует цельную модель GeckoLib (geo/block/&lt;машина&gt;.geo.json,
 * textures/block/&lt;машина&gt;.png и светящаяся _glow.png). Несобранное ядро рисуется обычной моделью блока.
 * <p>
 * Машина больше одного блока, поэтому рисуется и тогда, когда само ядро за краем экрана.
 */
public class MachineRenderer<T extends BlockEntity & GeoAnimatable & MultiblockHost> extends GeoBlockRenderer<T> {
    private static final double CULL_MARGIN = 20;
    private boolean glowPass;

    public MachineRenderer(String model) {
        super(new DefaultedBlockGeoModel<>(Warpbound.id(model)));
        addRenderLayer(new Glow<>(this));
    }

    @Override
    public void render(T machine, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        if (!machine.isFormed()) return;
        super.render(machine, partialTick, poseStack, bufferSource, packedLight, packedOverlay);
        if (machine instanceof PortedMachine ported && machine instanceof MultiblockCoreBlockEntity core) {
            float time = machine.getLevel() == null ? 0 : machine.getLevel().getGameTime() + partialTick;
            PortRenderer.draw(ported.clientPorts(), core.orientation(), poseStack, bufferSource, packedLight, packedOverlay, time, machine.getBlockState().getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.LIT));
        }
    }

    /** Меш без лишних объектов на каждую вершину: это главное время кадра у детальных машин. */
    @Override
    public void renderCube(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        double mark = cube.size().x;
        if (mark >= 0) {
            super.renderCube(poseStack, cube, buffer, packedLight, packedOverlay, colour);
            return;
        }
        if (glowPass && mark == MeshModelFactory.MESH_PLAIN) return;
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        for (GeoQuad quad : cube.quads()) {
            Vector3f q = quad.normal();
            float nx = n.m00() * q.x + n.m10() * q.y + n.m20() * q.z;
            float ny = n.m01() * q.x + n.m11() * q.y + n.m21() * q.z;
            float nz = n.m02() * q.x + n.m12() * q.y + n.m22() * q.z;
            for (GeoVertex v : quad.vertices()) {
                Vector3f p = v.position();
                buffer.addVertex(m.m00() * p.x + m.m10() * p.y + m.m20() * p.z + m.m30(),
                        m.m01() * p.x + m.m11() * p.y + m.m21() * p.z + m.m31(),
                        m.m02() * p.x + m.m12() * p.y + m.m22() * p.z + m.m32(),
                        colour, v.texU(), v.texV(), packedOverlay, packedLight, nx, ny, nz);
            }
        }
    }

    @Override
    public boolean shouldRenderOffScreen(T machine) {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 128;
    }

    @Override
    public boolean shouldRender(T machine, Vec3 camera) {
        Vec3 toMachine = Vec3.atCenterOf(machine.getBlockPos()).subtract(camera);
        double dist = toMachine.length();
        if (dist >= getViewDistance()) return false;
        // машина целиком за спиной камеры: запас на её размеры, чтобы большие модели не пропадали у края
        return dist < CULL_MARGIN || toMachine.dot(new Vec3(Minecraft.getInstance().gameRenderer.getMainCamera().getLookVector())) > 0;
    }

    /** Свечение (_glow.png) полной яркостью поверх модели: огонь, лампы, экраны. */
    public static final class Glow<T extends BlockEntity & GeoAnimatable> extends GeoRenderLayer<T> {
        public Glow(GeoRenderer<T> renderer) {
            super(renderer);
        }

        @Override
        public void render(PoseStack poseStack, T animatable, BakedGeoModel model, @Nullable RenderType renderType,
                           MultiBufferSource bufferSource, @Nullable VertexConsumer buffer, float partialTick,
                           int packedLight, int packedOverlay) {
            ResourceLocation tex = getRenderer().getTextureLocation(animatable);
            ResourceLocation glow = tex.withPath(p -> p.replace(".png", "_glow.png"));
            RenderType eyes = RenderType.eyes(glow);
            MachineRenderer<?> owner = getRenderer() instanceof MachineRenderer<?> r ? r : null;
            if (owner != null) owner.glowPass = true;
            getRenderer().reRender(model, poseStack, bufferSource, animatable, eyes, bufferSource.getBuffer(eyes), partialTick,
                    LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
            if (owner != null) owner.glowPass = false;
        }
    }
}
