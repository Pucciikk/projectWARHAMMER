package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.warpbound.industry.ChainMachineBlockEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;

/** Все машины цепочки — одна сущность, но модели разные: свой {@link MachineRenderer} на каждую, иначе GeckoLib пересобирает кости каждый кадр. */
public final class ChainMachineRenderer implements BlockEntityRenderer<ChainMachineBlockEntity> {
    private final Map<String, MachineRenderer<ChainMachineBlockEntity>> byModel = new HashMap<>();

    private MachineRenderer<ChainMachineBlockEntity> renderer(ChainMachineBlockEntity machine) {
        return byModel.computeIfAbsent(machine.modelName(), MachineRenderer::new);
    }

    @Override
    public void render(ChainMachineBlockEntity machine, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        renderer(machine).render(machine, partialTick, poseStack, bufferSource, packedLight, packedOverlay);
        if (machine.isFormed() && machine.getBlockState().is(dev.warpbound.core.WarpboundBlocks.LUMBER)) {
            LumberTrees.render(machine, poseStack, bufferSource, packedLight, packedOverlay);
        }
    }

    @Override
    public boolean shouldRenderOffScreen(ChainMachineBlockEntity machine) {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 128;
    }

    @Override
    public boolean shouldRender(ChainMachineBlockEntity machine, Vec3 camera) {
        return renderer(machine).shouldRender(machine, camera);
    }
}
