/**
 * pages/TreeView.jsx
 *
 * Исправления:
 * - handleSave корректно строит payload с family_id для новых персон
 * - Сиблинги: создаём через addParentChild для каждого общего родителя
 * - graph и members (enriched) передаются в PersonSidebar
 * - Убраны несуществующие поля из запросов
 */

import { useState, useEffect }     from "react";
import { useParams, Link }         from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2 } from "lucide-react";
import { Button }        from "@/components/ui/button";
import { toast }         from "@/components/ui/use-toast";
import LoadingSpinner    from "@/components/common/LoadingSpinner";
import TreeCanvas        from "@/components/tree/TreeCanvas";
import PersonSidebar     from "@/components/tree/PersonSidebar";
import AddPersonModal    from "@/components/tree/AddPersonModal";
import {
  personsApi,
  relationsApi,
  loadFamilyTree,
  createPersonAsChild,
  createPersonAsSpouse,
} from "@/api";
import { useAuth } from "@/lib/AuthContext";
import { ROUTES }  from "@/lib/routes";

export default function TreeView() {
  const { id: familyId } = useParams();
  const { user } = useAuth();

  const [family,         setFamily]         = useState(null);
  const [persons,        setPersons]        = useState([]); // enriched
  const [graph,          setGraph]          = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [showModal,      setShowModal]      = useState(false);
  const [relativePerson, setRelativePerson] = useState(null);
  const [editPerson,     setEditPerson]     = useState(null);
  const [isOwner,        setIsOwner]        = useState(false);

  useEffect(() => { loadData(); }, [familyId]);

  useEffect(() => {
    if (user && family) setIsOwner(family.owner_id === user.id);
  }, [user, family]);

  // Обновляем selectedPerson при изменении persons
  useEffect(() => {
    if (selectedPerson) {
      const updated = persons.find((p) => p.id === selectedPerson.id);
      if (updated) setSelectedPerson(updated);
    }
  }, [persons]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await loadFamilyTree(familyId);
      setFamily(data.family);
      setPersons(data.persons);
      setGraph(data.graph);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Ошибка загрузки",
        description: "Не удалось загрузить семейное дерево. Попробуйте обновить страницу.",
      });
    } finally {
      setLoading(false);
    }
  };

  // ── Управление модалкой ──────────────────────────────────────────────────
  const openAdd    = (relative = null) => { setRelativePerson(relative); setEditPerson(null);     setShowModal(true); };
  const openEdit   = (person)          => { setEditPerson(person);       setRelativePerson(null); setShowModal(true); };
  const closeModal = ()                => { setShowModal(false); setRelativePerson(null); setEditPerson(null); };

  // ── Сохранение ───────────────────────────────────────────────────────────
  const handleSave = async (formData, existingId, relationType, relPerson) => {
    try {
      if (existingId) {
        // PATCH: только поля first_name, last_name, gender, birth_date, death_date
        await personsApi.patch(existingId, formData);
        toast({ title: "Изменения сохранены" });
        await loadData();
        return;
      }

      // Базовый payload для создания
      const personPayload = {
        first_name: formData.first_name,
        last_name:  formData.last_name,
        gender:     formData.gender,
        birth_date: formData.birth_date || null,
        death_date: formData.death_date || null,
        family_id:  familyId,
      };

      if (relationType === "child" && relPerson) {
        await createPersonAsChild(personPayload, relPerson.id);
      } else if (relationType === "parent" && relPerson) {
        const newPerson = await personsApi.create(personPayload);
        await relationsApi.addParentChild({
          parent_id: newPerson.id,
          child_id:  relPerson.id,
          relation_type: "BIOLOGICAL",
        });
      } else if (relationType === "partner" && relPerson) {
        await createPersonAsSpouse(personPayload, relPerson.id);
      } else if (relationType === "sibling" && relPerson) {
        // Добавляем тех же родителей что и у relative
        const newPerson = await personsApi.create(personPayload);
        const parentIds = relPerson.parent_ids || [];
        await Promise.all(
          parentIds.map((pid) =>
            relationsApi.addParentChild({
              parent_id: pid,
              child_id:  newPerson.id,
              relation_type: "BIOLOGICAL",
            })
          )
        );
      } else {
        // Просто создаём без связей
        await personsApi.create(personPayload);
      }

      toast({ title: "Человек добавлен" });
      await loadData();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Неизвестная ошибка";
      toast({
        variant: "destructive",
        title: "Ошибка сохранения",
        description: typeof msg === "string" ? msg : "Проверьте данные и попробуйте снова.",
      });
    }
  };

  const handleDelete = async (personId) => {
    try {
      await personsApi.delete(personId);
      if (selectedPerson?.id === personId) setSelectedPerson(null);
      toast({ title: "Запись удалена" });
      await loadData();
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка удаления",
        description: "Не удалось удалить запись.",
      });
    }
  };

  const handleRemoveRelation = async (type, idA, idB) => {
    try {
      if (type === "parent_child") await relationsApi.removeParentChild(idA, idB);
      else if (type === "spouse")  await relationsApi.removeSpouse(idA, idB);
      toast({ title: "Связь удалена" });
      await loadData();
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка",
        description: "Не удалось удалить связь.",
      });
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────

  if (loading) return <LoadingSpinner fullScreen />;

  if (!family) {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Семья не найдена</p>
        <Link to={ROUTES.dashboard()}>
          <Button variant="outline" className="rounded-xl">← На главную</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col">
      <header className="flex items-center justify-between px-6 h-14 border-b bg-background/95 backdrop-blur z-20">
        <div className="flex items-center gap-3">
          <Link to={ROUTES.dashboard()}>
            <Button variant="ghost" size="sm" className="rounded-lg gap-1">
              <ChevronLeft className="w-4 h-4" /> Назад
            </Button>
          </Link>
          <div className="w-px h-5 bg-border" />
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center">
              <Leaf className="w-3 h-3 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">{family.name}</span>
          </div>
          <span className="text-sm text-muted-foreground">
            {graph?.meta?.node_count ?? persons.length} чел.
          </span>
        </div>

        <div className="flex gap-2">
          {!user          && <span className="text-sm text-muted-foreground px-2">Гость</span>}
          {user && !isOwner && <span className="text-sm text-muted-foreground px-2">Просмотр</span>}
          {isOwner && (
            <>
              <Button variant="outline" size="sm" className="rounded-lg">
                <Share2 className="w-4 h-4" />
              </Button>
              <Button size="sm" className="rounded-lg gap-1.5" onClick={() => openAdd(null)}>
                <UserPlus className="w-4 h-4" /> Добавить
              </Button>
            </>
          )}
        </div>
      </header>

      <div className="flex-1 flex relative overflow-hidden">
        <TreeCanvas
          members={persons}
          graph={graph}
          selectedPerson={selectedPerson}
          onSelectPerson={(p) => setSelectedPerson((prev) => (prev?.id === p.id ? null : p))}
          canEdit={isOwner}
          onAddChild={(parent) => openAdd(parent)}
        />

        <AnimatePresence>
          {selectedPerson && (
            <motion.div
              initial={{ x: 320 }} animate={{ x: 0 }} exit={{ x: 320 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute right-0 top-0 bottom-0 w-80 z-10"
            >
              <PersonSidebar
                person={selectedPerson}
                members={persons}
                graph={graph}
                onClose={() => setSelectedPerson(null)}
                canEdit={isOwner}
                onEdit={openEdit}
                onDelete={handleDelete}
                onAddRelative={(p) => openAdd(p)}
                onRemoveRelation={handleRemoveRelation}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AddPersonModal
        open={showModal}
        onClose={closeModal}
        onSave={handleSave}
        relativePerson={relativePerson}
        editPerson={editPerson}
      />
    </div>
  );
}
