package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.start.DataSlateItem;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;

public final class WarpboundItems {
    public static final Item DATA_SLATE_STORM = register("data_slate_storm", new DataSlateItem("storm"));
    public static final Item DATA_SLATE_NAVIGATOR = register("data_slate_navigator", new DataSlateItem("navigator"));
    public static final Item DATA_SLATE_SHIP = register("data_slate_ship", new DataSlateItem("ship"));
    public static final Item VOX_MODULE = register("vox_module", new TooltipItem(new Item.Properties()));
    public static final Item OMNISSIAH_SIGIL = register("omnissiah_sigil",
            new TooltipItem(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));
    public static final Item FORGE_SCHEMATIC = register("forge_schematic",
            new TooltipItem(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));
    public static final Item OBELISK_SCHEMATIC = register("obelisk_schematic",
            new TooltipItem(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));

    public static final CreativeModeTab TAB = Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, Warpbound.id("main"),
            FabricItemGroup.builder()
                    .title(Component.translatable("itemGroup.warpbound.main"))
                    .icon(() -> new ItemStack(OMNISSIAH_SIGIL))
                    .displayItems((params, out) -> {
                        out.accept(WarpboundBlocks.HULL_PLATING);
                        out.accept(WarpboundBlocks.SCORCHED_HULL_PLATING);
                        out.accept(WarpboundBlocks.BRASS_TRIM);
                        out.accept(WarpboundBlocks.VOX_BEACON);
                        out.accept(DATA_SLATE_STORM);
                        out.accept(DATA_SLATE_NAVIGATOR);
                        out.accept(DATA_SLATE_SHIP);
                        out.accept(VOX_MODULE);
                        out.accept(OMNISSIAH_SIGIL);
                        out.accept(FORGE_SCHEMATIC);
                        out.accept(OBELISK_SCHEMATIC);
                        out.accept(WarpboundEntities.TECH_PRIEST_SPAWN_EGG);
                        out.accept(WarpboundEntities.DARK_TECH_PRIEST_SPAWN_EGG);
                        out.accept(WarpboundEntities.DREADNOUGHT_SPAWN_EGG);
                    })
                    .build());

    private WarpboundItems() {
    }

    private static Item register(String name, Item item) {
        return Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), item);
    }

    public static void register() {
    }
}
