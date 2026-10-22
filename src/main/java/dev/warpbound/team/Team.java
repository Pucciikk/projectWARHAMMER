package dev.warpbound.team;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;

import java.util.LinkedHashSet;
import java.util.Set;
import java.util.UUID;

/**
 * Отряд: общие исследования и корабли лидера. Одиночка тоже живёт в отряде из одного человека,
 * поэтому особых случаев «а если без команды» в коде нет.
 */
public class Team {
    public final UUID id;
    public String name;
    public UUID leader;
    public final Set<UUID> members = new LinkedHashSet<>();

    Team(UUID id, String name, UUID leader) {
        this.id = id;
        this.name = name;
        this.leader = leader;
        members.add(leader);
    }

    public boolean solo() {
        return members.size() == 1;
    }

    CompoundTag save() {
        CompoundTag tag = new CompoundTag();
        tag.putUUID("id", id);
        tag.putString("name", name);
        tag.putUUID("leader", leader);
        ListTag list = new ListTag();
        for (UUID member : members) list.add(NbtUtils.createUUID(member));
        tag.put("members", list);
        return tag;
    }

    static Team load(CompoundTag tag) {
        Team team = new Team(tag.getUUID("id"), tag.getString("name"), tag.getUUID("leader"));
        for (Tag member : tag.getList("members", Tag.TAG_INT_ARRAY)) team.members.add(NbtUtils.loadUUID(member));
        return team;
    }
}
