import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2, Eye, EyeOff, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { base44 } from "@/api/base44Client";
import TreeCanvas from "../components/tree/TreeCanvas";
import PersonSidebar from "../components/tree/PersonSidebar";
import AddPersonModal from "../components/tree/AddPersonModal";

export default function TreeView() {
  const { id } = useParams();
  const [tree, setTree] = useState(null);
  const [members, setMembers] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [relativePerson, setRelativePerson] = useState(null); // person to link to
  const [editPerson, setEditPerson] = useState(null);         // person to edit
  const [isOwner, setIsOwner] = useState(false);

  useEffect(() => {
    const load = async () => {
      const isAuth = await base44.auth.isAuthenticated();
      if (isAuth) {
        const me = await base44.auth.me();
        setUser(me);
      }
      const [treeList, memberData] = await Promise.all([
        base44.entities.FamilyTree.filter({ id }),
        base44.entities.FamilyMember.filter({ tree_id: id }),
      ]);
      const treeObj = Array.isArray(treeList) ? treeList[0] : treeList;
      setTree(treeObj);
      setMembers(memberData || []);
      setLoading(false);
    };
    load();
  }, [id]);

  useEffect(() => {
    if (user && tree) setIsOwner(tree.created_by === user.email);
  }, [user, tree]);

  // Keep selectedPerson in sync with members list (after edits)
  useEffect(() => {
    if (selectedPerson) {
      const updated = members.find((m) => m.id === selectedPerson.id);
      if (updated) setSelectedPerson(updated);
    }
  }, [members]);

  const openAdd = (relative = null) => {
    setRelativePerson(relative);
    setEditPerson(null);
    setShowModal(true);
  };

  const openEdit = (person) => {
    setEditPerson(person);
    setRelativePerson(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setRelativePerson(null);
    setEditPerson(null);
  };

  /**
   * Save handler: either create (with optional relation back-linking) or update
   * relationType: "child" | "parent" | "partner" | "sibling"
   */
  const handleSave = async (data, existingId, relationType, relPerson) => {
    if (existingId) {
      // Edit existing
      const updated = await base44.entities.FamilyMember.update(existingId, data);
      setMembers((prev) => prev.map((m) => (m.id === existingId ? updated : m)));
    } else {
      // Create new
      const created = await base44.entities.FamilyMember.create(data);
      let updates = [created];

      // Back-link based on relation type
      if (relPerson && relationType) {
        if (relationType === "child") {
          // relPerson is parent — new member already has parent_ids set; nothing to back-link
        } else if (relationType === "parent") {
          // New member is parent of relPerson → add relPerson to new member's children indirectly
          // by adding created.id to relPerson's parent_ids
          const updatedRel = await base44.entities.FamilyMember.update(relPerson.id, {
            parent_ids: [...(relPerson.parent_ids || []), created.id],
          });
          updates = updates.map((u) => (u.id === relPerson.id ? updatedRel : u));
          setMembers((prev) => prev.map((m) => (m.id === relPerson.id ? updatedRel : m)));
        } else if (relationType === "partner") {
          // Link both ways
          const updatedNew = await base44.entities.FamilyMember.update(created.id, { partner_id: relPerson.id });
          const updatedRel = await base44.entities.FamilyMember.update(relPerson.id, { partner_id: created.id });
          updates = [updatedNew];
          setMembers((prev) => prev.map((m) => (m.id === relPerson.id ? updatedRel : m)));
        } else if (relationType === "sibling") {
          // New member already got same parent_ids as relPerson — nothing extra needed
        }
      }

      setMembers((prev) => {
        const withoutDupes = prev.filter((m) => !updates.some((u) => u.id === m.id));
        return [...withoutDupes, ...updates.filter((u) => !prev.some((p) => p.id === u.id)).concat(
          updates.filter((u) => prev.some((p) => p.id === u.id))
        )];
      });
      // Simpler: just refetch
      const fresh = await base44.entities.FamilyMember.filter({ tree_id: id });
      setMembers(fresh || []);
    }
  };

  const togglePublic = async () => {
    const updated = await base44.entities.FamilyTree.update(id, { is_public: !tree.is_public });
    setTree(updated);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: "hsl(40,33%,98%)" }}>
        <div className="text-center">
          <div className="text-5xl mb-4" style={{ animation: "float 3s ease-in-out infinite" }}>🌳</div>
          <div className="text-muted-foreground font-medium">Загрузка дерева...</div>
        </div>
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: "hsl(40,33%,98%)" }}>
        <div className="text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h2 className="font-serif text-xl font-semibold mb-2">Дерево не найдено</h2>
          <Link to="/dashboard">
            <Button variant="outline" className="rounded-xl mt-2">← Назад</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col" style={{ background: "hsl(40,33%,98%)" }}>

      {/* ─── Header ─── */}
      <header className="flex-shrink-0 flex items-center justify-between px-4 sm:px-6 h-14 z-20"
        style={{ borderBottom: "1px solid hsl(35,20%,88%)", background: "hsla(40,33%,98%,0.92)", backdropFilter: "blur(18px)" }}>

        <div className="flex items-center gap-3 min-w-0">
          <Link to="/dashboard">
            <Button variant="ghost" size="sm" className="rounded-xl gap-1 text-muted-foreground hover:text-foreground flex-shrink-0 px-2 sm:px-3">
              <ChevronLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Мои деревья</span>
            </Button>
          </Link>
          <div className="w-px h-5 bg-border flex-shrink-0" />
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
              style={{ background: "hsl(145,35%,88%)" }}>
              <Leaf className="w-3.5 h-3.5" style={{ color: "hsl(145,35%,38%)" }} />
            </div>
            <span className="font-serif font-semibold text-foreground truncate">{tree.name}</span>
          </div>
          <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-full text-xs"
            style={{ background: "hsl(35,40%,93%)", color: "hsl(30,10%,45%)" }}>
            <Users className="w-3 h-3" />
            {members.length} чел.
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Guest badge */}
          {!user && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-muted-foreground"
              style={{ background: "hsl(35,40%,93%)" }}>
              <Eye className="w-3.5 h-3.5" />
              Режим гостя
            </div>
          )}

          {/* Viewer (authenticated but not owner) */}
          {user && !isOwner && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs"
              style={{ background: "hsl(145,35%,92%)", color: "hsl(145,35%,28%)" }}>
              <Eye className="w-3.5 h-3.5" />
              Только просмотр
            </div>
          )}

          {/* Owner controls */}
          {isOwner && (
            <>
              <Button variant="outline" size="sm" className="rounded-xl gap-1.5 text-sm" onClick={togglePublic}>
                {tree.is_public
                  ? <><EyeOff className="w-3.5 h-3.5" /><span className="hidden sm:inline">Скрыть</span></>
                  : <><Share2 className="w-3.5 h-3.5" /><span className="hidden sm:inline">Поделиться</span></>
                }
              </Button>
              <Button size="sm"
                className="rounded-xl gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={() => openAdd(null)}>
                <UserPlus className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Добавить</span>
              </Button>
            </>
          )}
        </div>
      </header>

      {/* ─── Canvas + Sidebar ─── */}
      <div className="flex-1 flex relative overflow-hidden">
        <div className="flex-1 relative">
          <TreeCanvas
            members={members}
            selectedPerson={selectedPerson}
            onSelectPerson={(p) => setSelectedPerson(prev => prev?.id === p.id ? null : p)}
            canEdit={isOwner}
            onAddChild={(parent) => openAdd(parent)}
          />
        </div>

        <AnimatePresence>
          {selectedPerson && (
            <motion.div
              key="sidebar"
              initial={{ x: 320, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 320, opacity: 0 }}
              transition={{ type: "spring", stiffness: 340, damping: 32 }}
              className="absolute right-0 top-0 bottom-0 w-80 z-10 shadow-2xl"
            >
              <PersonSidebar
                person={selectedPerson}
                members={members}
                onClose={() => setSelectedPerson(null)}
                canEdit={isOwner}
                onEdit={openEdit}
                onAddRelative={(p) => openAdd(p)}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ─── Modal ─── */}
      <AddPersonModal
        open={showModal}
        onClose={closeModal}
        onSave={handleSave}
        treeId={id}
        relativePerson={relativePerson}
        editPerson={editPerson}
      />
    </div>
  );
}