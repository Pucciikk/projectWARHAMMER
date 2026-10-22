package dev.warpbound.core;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.resource.IdentifiableResourceReloadListener;
import net.fabricmc.fabric.api.resource.ResourceManagerHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimpleJsonResourceReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;

/**
 * Реестр из датапака: data/&lt;ns&gt;/&lt;dir&gt;/*.json, перезагружается по /reload.
 * Битая запись пишется в лог и пропускается, игра не падает.
 */
public class DataRegistry<T> extends SimpleJsonResourceReloadListener implements IdentifiableResourceReloadListener {
    private static final Gson GSON = new GsonBuilder().create();

    private final String dir;
    private final Codec<T> codec;
    private final List<Consumer<DataRegistry<T>>> listeners = new ArrayList<>();
    private Map<ResourceLocation, T> entries = Map.of();

    public DataRegistry(String dir, Codec<T> codec) {
        super(GSON, dir);
        this.dir = dir;
        this.codec = codec;
        ResourceManagerHelper.get(PackType.SERVER_DATA).registerReloadListener(this);
    }

    @Override
    protected void apply(Map<ResourceLocation, JsonElement> jsons, ResourceManager manager, ProfilerFiller profiler) {
        Map<ResourceLocation, T> loaded = new LinkedHashMap<>();
        jsons.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(e -> codec.parse(JsonOps.INSTANCE, e.getValue())
                        .resultOrPartial(err -> Warpbound.LOG.error("{}: {}: {}", dir, e.getKey(), err))
                        .ifPresent(value -> loaded.put(e.getKey(), value)));
        entries = Collections.unmodifiableMap(loaded);
        Warpbound.LOG.info("{}: загружено записей: {}", dir, entries.size());
        listeners.forEach(l -> l.accept(this));
    }

    /** Вызывается после каждой загрузки, например для проверки ссылок между записями. */
    public void onReload(Consumer<DataRegistry<T>> listener) {
        listeners.add(listener);
    }

    public Optional<T> get(ResourceLocation id) {
        return Optional.ofNullable(entries.get(id));
    }

    public Map<ResourceLocation, T> all() {
        return entries;
    }

    public Codec<T> codec() {
        return codec;
    }

    @Override
    public ResourceLocation getFabricId() {
        return Warpbound.id(dir);
    }
}
