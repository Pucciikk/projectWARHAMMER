package dev.warpbound.gun;

import dev.warpbound.Warpbound;
import dev.warpbound.gear.GeoGear;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.BlockPos;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.animatable.client.GeoRenderProvider;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;
import java.util.function.Consumer;

/**
 * Огнестрельное оружие: ЛКМ стрелять, ПКМ целиться, R перезарядка. Патроны лежат в компоненте предмета.
 * Здесь то, что завязано на анимацию и механику (темп, ёмкость, время перезарядки: совпадает с длиной клипа).
 * Урон, скорость снаряда и разброс — в data/warpbound/gun/&lt;предмет&gt;.json.
 */
public class GunItem extends Item implements GeoItem {
    public enum Kind {LAS, BOLT}

    /** interval — тиков между выстрелами; reloadTicks — длина клипа перезарядки; ammo — чем заряжается. */
    public record Mechanics(Kind kind, int magSize, int interval, int reloadTicks, ResourceLocation ammo, boolean automatic) {
    }

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    public final Mechanics mechanics;

    public GunItem(Properties properties, Mechanics mechanics) {
        super(properties.stacksTo(1).component(GunComponents.AMMO, 0));
        this.mechanics = mechanics;
    }

    public Item ammoItem() {
        return BuiltInRegistries.ITEM.get(mechanics.ammo());
    }

    public static int ammo(ItemStack stack) {
        return stack.getOrDefault(GunComponents.AMMO, 0);
    }

    public static void setAmmo(ItemStack stack, int value) {
        stack.set(GunComponents.AMMO, value);
    }

    /** Все действия идут через свой пакет, поэтому обычное использование не должно ни махать рукой, ни открывать ничего. */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        return InteractionResultHolder.pass(player.getItemInHand(hand));
    }

    /** Оружием нельзя случайно ломать блоки. */
    @Override
    public boolean canAttackBlock(BlockState state, Level level, BlockPos pos, Player player) {
        return false;
    }

    @Override
    public boolean isBarVisible(ItemStack stack) {
        return ammo(stack) < mechanics.magSize();
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13f * ammo(stack) / mechanics.magSize());
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return mechanics.kind() == Kind.LAS ? 0xE8452E : 0xE0B040;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("item.warpbound.gun.ammo", ammo(stack), mechanics.magSize()).withStyle(ChatFormatting.GOLD));
        tooltip.add(Component.translatable("item.warpbound.gun.ammo_item", ammoItem().getDescription()).withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("item.warpbound.gun.controls").withStyle(ChatFormatting.DARK_GRAY));
    }

    /** Смена патронов в компоненте не должна перезапускать ванильное «поднять предмет». */
    @Override
    public boolean allowComponentsUpdateAnimation(Player player, InteractionHand hand, ItemStack oldStack, ItemStack newStack) {
        return false;
    }

    @Override
    public boolean isValidRepairItem(ItemStack stack, ItemStack repair) {
        return false;
    }

    @Override
    public void createGeoRenderer(Consumer<GeoRenderProvider> consumer) {
        GeoGear.RENDER.accept(this, consumer);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    static ResourceLocation id(String path) {
        return Warpbound.id(path);
    }
}
