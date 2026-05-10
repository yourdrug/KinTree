/**
 * pages/TreeView.jsx
 *
 * ИСПРАВЛЕНИЯ:
 * 1. loadData обёрнут в useCallback — стабильная ссылка, нет бесконечных рендеров.
 * 2. useEffect для обновления selectedPerson использует ref-based подход —
 *    не вызывает loadData снова при изменении persons.
 * 3. Убрана зависимость от persons в useEffect ([persons]) которая ранее
 *    могла вызвать бесконечный цикл: loadData → setPersons → effect → loadData.
 * 4. Стабильные deps во всех useEffect.
 */

import { useState, useEffect, useCallback, useRef } from "react";
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
  const [persons,        setPersons]        = useState([]);
  const [graph,          setGraph]          = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [showModal,      setShowModal]      = useState(false);
  const [relativePerson, setRelativePerson] = useState(null);
  const [editPerson,     setEditPerson]     = useState(null);
  const [isOwner,        setIsOwner]        = useState(false);

  // Ref для синхронизации selectedPerson без лишних рендеров
  const selectedIdRef = useRef(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await loadFamilyTree(familyId);
      setFamily(data.family);
      setPersons(data.persons);
      setGraph(data.graph);

      // Обновляем selectedPerson если он был выбран — через ref, без зависимости от стейта
      if (selectedIdRef.current) {
        const updated = data.persons.find((p) => p.id === selectedIdRef.current);
        setSelectedPerson(updated || null);
        if (!updated) selectedIdRef.current = null;
      }
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка загрузки",
        description: "Не удалось загрузить семейное дерево. Попробуйте обновить страницу.",
      });
    } finally {
      setLoading(false);
    }
  }, [familyId]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (user && family) setIsOwner(family.owner_id === user.id);
  }, [user, family]);

  const handleSelectPerson = useCallback((p) => {
    setSelectedPerson((prev) => {
      if (prev?.id === p.id) {
        selectedIdRef.current = null;
        return null;
      }
      selectedIdRef.current = p.id;
      return p;
    });
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSelectedPerson(null);
    selectedIdRef.current = null;
  }, []);

  // ── Управление модалкой ──────────────────────────────────────────────────
  const openAdd    = useCallback((relative = null) => { setRelativePerson(relative); setEditPerson(null);     setShowModal(true); }, []);
  const openEdit   = useCallback((person)          => { setEditPerson(person);       setRelativePerson(null); setShowModal(true); }, []);
  const closeModal = useCallback(()                => { setShowModal(false); setRelativePerson(null); setEditPerson(null); }, []);

  // ── Сохранение ───────────────────────────────────────────────────────────
  const handleSave = useCallback(async (formData, existingId, relationType, relPerson) => {
    try {
      if (existingId) {
        await personsApi.patch(existingId, formData);
        toast({ title: "Изменения сохранены" });
        await loadData();
        return;
      }

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
  }, [familyId, loadData]);

  const handleDelete = useCallback(async (personId) => {
    try {
      await personsApi.delete(personId);
      if (selectedIdRef.current === personId) {
        setSelectedPerson(null);
        selectedIdRef.current = null;
      }
      toast({ title: "Запись удалена" });
      await loadData();
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка удаления",
        description: "Не удалось удалить запись.",
      });
    }
  }, [loadData]);

  const handleRemoveRelation = useCallback(async (type, idA, idB) => {
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
  }, [loadData]);

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
          onSelectPerson={handleSelectPerson}
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
                onClose={handleCloseSidebar}
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
