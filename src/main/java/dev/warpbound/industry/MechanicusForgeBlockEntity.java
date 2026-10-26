package dev.warpbound.industry;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.faction.Faction;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import dev.warpbound.operator.TechPriestEntity;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.AABB;

/**
 * Кузня Механикус 5×5×6 — рабочее место техножреца (глава 2). Освящается Омниссианским ключом.
 * Когда техножрец рядом, кузня оживает: горн разгорается, молоты на сервоплечах бьют по наковальне.
 */
public class MechanicusForgeBlockEntity extends MachineCoreBlockEntity {
    private static final double PRIEST_RANGE = 10;

    public MechanicusForgeBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.MECHANICUS_FORGE, pos, state, Warpbound.id("mechanicus_forge"));
    }

    @Override
    public String modelName() {
        return "mechanicus_forge";
    }

    @Override
    public boolean isWorking() {
        return getBlockState().getValue(BlockStateProperties.LIT);
    }

    @Override
    public void onFormedBy(ServerPlayer player) {
        QuestManager.setFlag(player, StoryFlags.MECHANICUS_FORGE_BUILT);
    }

    @Override
    public void onUnformed(ServerLevel level) {
        setLit(level, false);
    }

    @Override
    public void tickFormed(ServerLevel level) {
        if (level.getGameTime() % 20 != 0) return;
        boolean priest = !level.getEntitiesOfClass(TechPriestEntity.class, new AABB(getBlockPos()).inflate(PRIEST_RANGE),
                p -> p.faction() == Faction.IMPERIUM && p.isAlive()).isEmpty();
        setLit(level, priest);
    }

    private void setLit(ServerLevel level, boolean lit) {
        BlockState state = getBlockState();
        if (state.getValue(BlockStateProperties.LIT) != lit) {
            level.setBlock(getBlockPos(), state.setValue(BlockStateProperties.LIT, lit), Block.UPDATE_ALL);
        }
    }
}
