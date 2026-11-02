package dev.warpbound.industry;

import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.faction.Faction;
import dev.warpbound.operator.TechPriestEntity;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * Кузня Механикус: центральный сборщик компонентов, рецепты из цепочки. Постройка открывает квест;
 * когда техножрец рядом, кузня работает вдвое быстрее: он ведёт молоты сам.
 */
public class MechanicusForgeBlockEntity extends ChainMachineBlockEntity {
    private static final double PRIEST_RANGE = 10;
    private static final int PRIEST_RECHECK = 40;
    private boolean priestNear;

    public MechanicusForgeBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.MECHANICUS_FORGE, pos, state);
    }

    @Override
    public void onFormedBy(ServerPlayer player) {
        QuestManager.setFlag(player, StoryFlags.MECHANICUS_FORGE_BUILT);
    }

    @Override
    protected double speedBonus(ServerLevel level) {
        if (level.getGameTime() % PRIEST_RECHECK == 0) {
            priestNear = !level.getEntitiesOfClass(TechPriestEntity.class, new AABB(getBlockPos()).inflate(PRIEST_RANGE),
                    p -> p.faction() == Faction.IMPERIUM && p.isAlive()).isEmpty();
        }
        return priestNear ? 2 : 1;
    }
}
