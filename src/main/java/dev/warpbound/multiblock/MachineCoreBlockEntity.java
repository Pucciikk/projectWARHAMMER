package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.function.BooleanSupplier;

/**
 * Ядро машины с цельной моделью: после освящения груда блоков прячется, ядро рисует модель GeckoLib
 * geo/block/&lt;машина&gt;.geo.json (см. {@code MachineRenderer} на клиенте).
 * <p>
 * Анимации по контракту: {@code misc.idle} — стоит собранная, {@code work.active} — работает
 * ({@link #isWorking()}), разовые действия (удар пресса, удар молота) — через {@link #triggerAnim}.
 */
public abstract class MachineCoreBlockEntity extends MultiblockCoreBlockEntity implements GeoBlockEntity {
    public static final String ACTION = "action";
    protected static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    protected static final RawAnimation WORK = RawAnimation.begin().thenLoop("work.active");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    protected MachineCoreBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state, ResourceLocation definitionId) {
        super(type, pos, state, definitionId);
    }

    /** Имя модели (geo/block/&lt;имя&gt;.geo.json). */
    public abstract String modelName();

    /** Работает ли сейчас — модель играет work.active. Считается на клиенте, данные должны быть в состоянии блока. */
    public boolean isWorking() {
        return false;
    }

    /** Разовые анимации машины (имена из файла анимаций). */
    protected String[] actions() {
        return new String[0];
    }

    @Override
    public boolean hidesMembers() {
        return true;
    }

    /** Машины главы 1 освящаются пустой рукой; остальные — Омниссианским ключом. */
    protected boolean formsByHand() {
        return false;
    }

    @Override
    public boolean formsWith(ItemStack stack) {
        return formsByHand() ? stack.isEmpty() : super.formsWith(stack);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        addControllers(this, this, this::isWorking, controllers, actions());
    }

    /** Общие контроллеры машин: и для ядер на этом классе, и для машин с другим базовым классом (горн — печь). */
    public static <T extends GeoBlockEntity> void addControllers(T be, MultiblockHost host, BooleanSupplier working,
                                                                 AnimatableManager.ControllerRegistrar controllers, String... actions) {
        controllers.add(new AnimationController<>(be, "main", 8, state -> {
            if (!host.isFormed()) return PlayState.STOP;
            return state.setAndContinue(working.getAsBoolean() ? WORK : IDLE);
        }));
        AnimationController<T> action = new AnimationController<>(be, ACTION, 0, state -> PlayState.STOP);
        for (String name : actions) action.triggerableAnim(name, RawAnimation.begin().thenPlay(name));
        controllers.add(action);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
