package dev.warpbound.industry;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockController;
import dev.warpbound.multiblock.MultiblockHost;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.AbstractFurnaceBlock;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Горн обломков: печь, которая знает только рецепты переплавки корабельного лома.
 * Мультиблок 3×3×3 (data/warpbound/multiblock/salvage_forge.json): ядро — печь в середине переднего ряда.
 * Собирается ПКМ пустой рукой; собранный рисуется цельной моделью и только тогда плавит.
 */
public class SalvageForgeBlockEntity extends AbstractFurnaceBlockEntity implements MultiblockHost, GeoBlockEntity {
    private final MultiblockController multiblock = new MultiblockController(this, Warpbound.id("salvage_forge"));
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public SalvageForgeBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.SALVAGE_FORGE, pos, state, WarpboundRecipes.SALVAGING);
    }

    @Override
    public MultiblockController multiblock() {
        return multiblock;
    }

    @Override
    public boolean hidesMembers() {
        return true;
    }

    @Override
    public boolean formsWith(ItemStack stack) {
        return stack.isEmpty();
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("block.warpbound.salvage_forge");
    }

    @Override
    protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
        return new SalvageForgeMenu(id, inventory, this, dataAccess);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        MachineCoreBlockEntity.addControllers(this, this, () -> getBlockState().getValue(AbstractFurnaceBlock.LIT), controllers);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        multiblock.save(tag);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        multiblock.load(tag);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        multiblock.writeUpdateTag(tag);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
