package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.gear.ChainswordItem;
import dev.warpbound.gear.GeoArmorItem;
import dev.warpbound.gear.LasgunItem;
import dev.warpbound.gear.WarpboundArmor;
import dev.warpbound.multiblock.OmnissianKeyItem;
import dev.warpbound.ship.TeleportHomerItem;
import dev.warpbound.start.DataSlateItem;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ArmorItem;
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
    // ---- Сезон 1: компоненты оружия и брони (docs/content/season1-items.md)
    /** Фокусирующая линза: собирает луч лазгана. */
    public static final Item FOCUSING_LENS = register("focusing_lens", new Item(new Item.Properties()));
    /** Капаситор: накопитель заряда — лазпакеты, позже буфер сети. */
    public static final Item CAPACITOR = register("capacitor", new Item(new Item.Properties()));
    /** Лазпакет: магазин лазгана. */
    public static final Item LAS_BATTERY = register("las_battery", new TooltipItem(new Item.Properties().stacksTo(16)));
    /** Разряженный лазпакет: аварийная зарядка — в костре (из лора), с риском потери ёмкости позже. */
    public static final Item LAS_BATTERY_DEPLETED = register("las_battery_depleted", new TooltipItem(new Item.Properties().stacksTo(16)));
    /** Сервопривод: мотор механизмов и цепного оружия. */
    public static final Item SERVO_MOTOR = register("servo_motor", new Item(new Item.Properties()));
    /** Цепное полотно: зубчатая цепь цепного меча, им же меч и чинится. */
    public static final Item CHAIN_BLADE = register("chain_blade", new Item(new Item.Properties()));
    /** Флак-пластина: слоёная пластина брони Гвардии. */
    public static final Item FLAK_PLATE = register("flak_plate", new Item(new Item.Properties()));
    /** Фильтр респиратора. */
    public static final Item RESPIRATOR_FILTER = register("respirator_filter", new Item(new Item.Properties()));
    // ---- Сезон 1: оружие и броня
    public static final Item LASGUN = register("lasgun", new LasgunItem(new Item.Properties().stacksTo(1).durability(31)));
    public static final Item CHAINSWORD = register("chainsword", new ChainswordItem(new Item.Properties()));
    public static final Item FLAK_HELMET = register("flak_helmet", armor(WarpboundArmor.FLAK, ArmorItem.Type.HELMET, 18));
    public static final Item FLAK_CHESTPLATE = register("flak_chestplate", armor(WarpboundArmor.FLAK, ArmorItem.Type.CHESTPLATE, 18));
    public static final Item FLAK_LEGGINGS = register("flak_leggings", armor(WarpboundArmor.FLAK, ArmorItem.Type.LEGGINGS, 18));
    public static final Item FLAK_BOOTS = register("flak_boots", armor(WarpboundArmor.FLAK, ArmorItem.Type.BOOTS, 18));
    /** Респиратор: слот шлема (отдельного слота лица пока нет), на Кинерисе защищает от ядовитого воздуха. */
    public static final Item RESPIRATOR = register("respirator", new GeoArmorItem(WarpboundArmor.RESPIRATOR, ArmorItem.Type.HELMET,
            new Item.Properties().durability(ArmorItem.Type.HELMET.getDurability(12)), true));
    /** Пустая колба для пробы: её заправляют в варп-пробоотборник анклава. */
    public static final Item SAMPLE_VIAL = register("sample_vial", new TooltipItem(new Item.Properties().stacksTo(16)));
    /** Образец варп-материи: красная взвесь из порта пробоотборника, взятая в варпе. Сырьё для исследований. */
    public static final Item WARP_SAMPLE = register("warp_sample", new TooltipItem(new Item.Properties().stacksTo(16).rarity(Rarity.RARE)));

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
                        out.accept(WarpboundBlocks.STAR_CHART);
                        out.accept(WarpboundBlocks.GRAV_LIFT);
                        out.accept(WarpboundBlocks.WARP_SAMPLER);
                        out.accept(SAMPLE_VIAL);
                        for (Item i : new Item[]{FOCUSING_LENS, CAPACITOR, LAS_BATTERY, LAS_BATTERY_DEPLETED, SERVO_MOTOR, CHAIN_BLADE,
                                FLAK_PLATE, RESPIRATOR_FILTER, LASGUN, CHAINSWORD, FLAK_HELMET, FLAK_CHESTPLATE, FLAK_LEGGINGS,
                                FLAK_BOOTS, RESPIRATOR}) {
                            out.accept(i);
                        }
                        out.accept(WARP_SAMPLE);
                        out.accept(WarpboundBlocks.WARP_DRIVE);
                        out.accept(WarpboundBlocks.IMPERIAL_STANDARD);
                        out.accept(WarpboundBlocks.IMPERIAL_STANDARD_POLE);
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

    private static Item armor(net.minecraft.core.Holder<net.minecraft.world.item.ArmorMaterial> material, ArmorItem.Type type, int durability) {
        return new GeoArmorItem(material, type, new Item.Properties().durability(type.getDurability(durability)), false);
    }

    private static Item register(String name, Item item) {
        return Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), item);
    }

    public static void register() {
    }
}
