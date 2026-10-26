package dev.warpbound.ship.block;

import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/** Крупное корабельное оборудование: только анимация модели (плазма реактора, кольца Геллера, голокарта). */
public class ShipFixtureBlockEntity extends BlockEntity implements GeoBlockEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public ShipFixtureBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.SHIP_FIXTURE, pos, state);
    }

    /** Имя модели = id блока: reactor_core, geller_node, nav_table, auspex, teleportarium_pad. */
    public String modelName() {
        return BuiltInRegistries.BLOCK.getKey(getBlockState().getBlock()).getPath();
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 0, state -> state.setAndContinue(IDLE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
