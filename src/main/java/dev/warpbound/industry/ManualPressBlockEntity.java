package dev.warpbound.industry;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/** Собранный ручной пресс: винтовой пресс со штурвалом; каждый удар игрока — анимация work.strike. */
public class ManualPressBlockEntity extends MachineCoreBlockEntity {
    public static final String STRIKE = "work.strike";

    public ManualPressBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.MANUAL_PRESS, pos, state, Warpbound.id("manual_press"));
    }

    @Override
    public String modelName() {
        return "manual_press";
    }

    @Override
    protected boolean formsByHand() {
        return true;
    }

    @Override
    protected String[] actions() {
        return new String[]{STRIKE};
    }

    void strike() {
        triggerAnim(ACTION, STRIKE);
    }
}
