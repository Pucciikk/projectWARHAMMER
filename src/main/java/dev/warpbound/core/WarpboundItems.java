package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.multiblock.OmnissianKeyItem;
import dev.warpbound.ship.TeleportHomerItem;
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
    /** Схема стапеля: её передаёт техножрец, без неё пульт верфи не собрать. */
    public static final Item SHIPYARD_SCHEMATIC = register("shipyard_schematic",
            new TooltipItem(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));
    /** Корабельный лом и детали Сезона 1: пласталь до прометия добывается только переплавкой лома. */
    public static final Item PLASTEEL_INGOT = register("plasteel_ingot", new Item(new Item.Properties()));
    /** Запасной путь к пластали, когда лом на сервере кончился: долгая переплавка в горне. */
    public static final Item PLASTEEL_BLEND = register("plasteel_blend", new TooltipItem(new Item.Properties()));
    public static final Item BRASS_INGOT = register("brass_ingot", new Item(new Item.Properties()));
    public static final Item PLASTEEL_PLATE = register("plasteel_plate", new Item(new Item.Properties()));
    public static final Item BRASS_GEAR = register("brass_gear", new Item(new Item.Properties()));
    public static final Item TELEPORT_HOMER = register("teleport_homer", new TeleportHomerItem(new Item.Properties().stacksTo(1)));
    public static final Item OMNISSIAN_KEY = register("omnissian_key", new OmnissianKeyItem(new Item.Properties().stacksTo(1)));

    public static final CreativeModeTab TAB = Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, Warpbound.id("main"),
            FabricItemGroup.builder()
                    .title(Component.translatable("itemGroup.warpbound.main"))
                    .icon(() -> new ItemStack(OMNISSIAH_SIGIL))
                    .displayItems((params, out) -> {
                        out.accept(WarpboundBlocks.HULL_PLATING);
                        out.accept(WarpboundBlocks.SCORCHED_HULL_PLATING);
                        out.accept(WarpboundBlocks.BRASS_TRIM);
                        out.accept(WarpboundBlocks.VOX_BEACON);
                        out.accept(WarpboundBlocks.DOCK_GIRDER);
                        out.accept(WarpboundBlocks.SHIPYARD_CONSOLE);
                        out.accept(OMNISSIAN_KEY);
                        out.accept(TELEPORT_HOMER);
                        out.accept(WarpboundBlocks.NAV_TABLE);
                        out.accept(WarpboundBlocks.AUSPEX);
                        out.accept(WarpboundBlocks.GELLER_NODE);
                        out.accept(WarpboundBlocks.REACTOR_CORE);
                        out.accept(WarpboundBlocks.TELEPORTARIUM_PAD);
                        out.accept(WarpboundBlocks.COMMAND_THRONE);
                        out.accept(WarpboundBlocks.COMMAND_CONSOLE);
                        out.accept(WarpboundBlocks.SALVAGE_FORGE);
                        out.accept(WarpboundBlocks.MANUAL_PRESS);
                        out.accept(WarpboundBlocks.MECHANICUS_FORGE);
                        WarpboundBuildingBlocks.ALL.forEach(out::accept);
                        WarpboundBuildingBlocks.ITEMS.forEach(out::accept);
                        out.accept(PLASTEEL_INGOT);
                        out.accept(PLASTEEL_BLEND);
                        out.accept(BRASS_INGOT);
                        out.accept(PLASTEEL_PLATE);
                        out.accept(BRASS_GEAR);
                        out.accept(DATA_SLATE_STORM);
                        out.accept(DATA_SLATE_NAVIGATOR);
                        out.accept(DATA_SLATE_SHIP);
                        out.accept(VOX_MODULE);
                        out.accept(OMNISSIAH_SIGIL);
                        out.accept(FORGE_SCHEMATIC);
                        out.accept(OBELISK_SCHEMATIC);
                        out.accept(SHIPYARD_SCHEMATIC);
                        out.accept(WarpboundEntities.TECH_PRIEST_SPAWN_EGG);
                        out.accept(WarpboundEntities.DARK_TECH_PRIEST_SPAWN_EGG);
                        out.accept(WarpboundEntities.DREADNOUGHT_SPAWN_EGG);
                        out.accept(WarpboundEntities.SERVITOR_SPAWN_EGG);
                        out.accept(WarpboundEntities.CULTIST_SPAWN_EGG);
                        out.accept(WarpboundEntities.BLOODLETTER_SPAWN_EGG);
                        out.accept(WarpboundEntities.PINK_HORROR_SPAWN_EGG);
                        out.accept(WarpboundEntities.BLUE_HORROR_SPAWN_EGG);
                        out.accept(WarpboundEntities.POSSESSED_PRIEST_SPAWN_EGG);
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
