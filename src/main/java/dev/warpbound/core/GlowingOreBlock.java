package dev.warpbound.core;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Vector3f;

/** Светящаяся руда (радий, варп-камень): своим цветом искрит на открытых гранях. */
public class GlowingOreBlock extends DropExperienceBlock {
    public static final MapCodec<GlowingOreBlock> CODEC = simpleCodec(p -> new GlowingOreBlock(ConstantInt.of(0), 0xFFFFFF, p));
    private final DustParticleOptions dust;

    public GlowingOreBlock(IntProvider xp, int color, Properties properties) {
        super(xp, properties);
        this.dust = new DustParticleOptions(new Vector3f(((color >> 16) & 255) / 255f, ((color >> 8) & 255) / 255f, (color & 255) / 255f), 0.8f);
    }

    @Override
    public MapCodec<? extends DropExperienceBlock> codec() {
        return CODEC;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(3) != 0) return;
        Direction d = Direction.getRandom(random);
        BlockPos side = pos.relative(d);
        if (level.getBlockState(side).isSolidRender(level, side)) return;
        double x = pos.getX() + 0.5 + d.getStepX() * 0.55 + (d.getStepX() == 0 ? random.nextDouble() - 0.5 : 0);
        double y = pos.getY() + 0.5 + d.getStepY() * 0.55 + (d.getStepY() == 0 ? random.nextDouble() - 0.5 : 0);
        double z = pos.getZ() + 0.5 + d.getStepZ() * 0.55 + (d.getStepZ() == 0 ? random.nextDouble() - 0.5 : 0);
        level.addParticle(dust, x, y, z, 0, 0, 0);
    }
}
