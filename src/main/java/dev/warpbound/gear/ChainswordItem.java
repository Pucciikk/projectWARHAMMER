package dev.warpbound.gear;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundItems;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.sounds.SoundEvent;
import org.joml.Vector3f;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Block;
import net.minecraft.tags.TagKey;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.animatable.client.GeoRenderProvider;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.function.Consumer;

/**
 * Цепной меч: тяжёлый медленный клинок с бегущей цепью — брызги, искры и рёв мотора при каждом ударе.
 * Удержание ЛКМ бьёт удар за ударом (ChainswordClient), темп задан атрибутом скорости атаки.
 */
public class ChainswordItem extends SwordItem implements GeoItem {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    /** Ступень цепного оружия: прочнее железа, чинится цепным полотном. */
    public static final Tier CHAIN = new Tier() {
        @Override
        public int getUses() {
            return 600;
        }

        @Override
        public float getSpeed() {
            return 7f;
        }

        @Override
        public float getAttackDamageBonus() {
            return 3f;
        }

        @Override
        public TagKey<Block> getIncorrectBlocksForDrops() {
            return BlockTags.INCORRECT_FOR_IRON_TOOL;
        }

        @Override
        public int getEnchantmentValue() {
            return 10;
        }

        @Override
        public Ingredient getRepairIngredient() {
            return Ingredient.of(WarpboundItems.CHAIN_BLADE);
        }
    };

    public ChainswordItem(Properties properties) {
        super(CHAIN, properties.attributes(SwordItem.createAttributes(CHAIN, 4, -2.9f)));
    }

    @Override
    public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (attacker.level() instanceof ServerLevel sl) {
            sl.playSound(null, target.blockPosition(), SoundEvent.createVariableRangeEvent(Warpbound.id("gun.chainsword_bite")), SoundSource.PLAYERS, 1.0f, 0.92f + sl.random.nextFloat() * 0.16f);
            double y = target.getY(0.62);
            // кровь и искры летят от цепи, в сторону удара
            sl.sendParticles(new DustParticleOptions(new Vector3f(0.5f, 0.02f, 0.02f), 1.4f), target.getX(), y, target.getZ(), 24, 0.22, 0.28, 0.22, 0.12);
            sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.REDSTONE_BLOCK.defaultBlockState()), target.getX(), y, target.getZ(), 10, 0.2, 0.25, 0.2, 0.15);
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, target.getX(), y, target.getZ(), 10, 0.15, 0.2, 0.15, 0.25);
        }
        return super.hurtEnemy(stack, target, attacker);
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
}
