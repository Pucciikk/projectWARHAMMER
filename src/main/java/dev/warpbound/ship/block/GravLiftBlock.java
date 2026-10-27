package dev.warpbound.ship.block;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Гравилифт: площадка в полу. ПКМ — подъём к следующему гравилифту над ней по той же вертикали,
 * а если сверху нет — спуск к ближайшему снизу. Так связаны палубы корабля (анклав ↔ мостик).
 */
public class GravLiftBlock extends Block {
    /** Сколько блоков вверх и вниз ищем пару. */
    private static final int REACH = 48;
    private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 2, 16);

    public GravLiftBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide || !(player instanceof ServerPlayer sp)) return InteractionResult.SUCCESS;
        BlockPos target = find(level, pos, 1);
        boolean up = target != null;
        if (target == null) target = find(level, pos, -1);
        if (target == null) {
            sp.displayClientMessage(Component.translatable("block.warpbound.grav_lift.none").withStyle(ChatFormatting.GRAY), true);
            return InteractionResult.CONSUME;
        }
        ServerLevel sl = sp.serverLevel();
        sl.sendParticles(ParticleTypes.REVERSE_PORTAL, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 30, 0.3, 0.8, 0.3, 0.02);
        sl.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 0.8f, up ? 1.4f : 0.8f);
        sp.teleportTo(sl, target.getX() + 0.5, target.getY() + 0.125, target.getZ() + 0.5, sp.getYRot(), sp.getXRot());
        sl.sendParticles(ParticleTypes.REVERSE_PORTAL, target.getX() + 0.5, target.getY() + 1, target.getZ() + 0.5, 30, 0.3, 0.8, 0.3, 0.02);
        sl.playSound(null, target, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 0.8f, up ? 1.4f : 0.8f);
        sp.displayClientMessage(Component.translatable(up ? "block.warpbound.grav_lift.up" : "block.warpbound.grav_lift.down")
                .withStyle(ChatFormatting.AQUA), true);
        return InteractionResult.CONSUME;
    }

    private BlockPos find(Level level, BlockPos from, int dir) {
        for (int i = 2; i <= REACH; i++) {
            BlockPos p = from.above(i * dir);
            if (level.getBlockState(p).is(this)) return p;
        }
        return null;
    }
}
