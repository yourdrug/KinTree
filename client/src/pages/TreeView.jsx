import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2, Eye, EyeOff, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import TreeCanvas from "../components/tree/TreeCanvas";
import PersonSidebar from "../components/tree/PersonSidebar";
import AddPersonModal from "../components/tree/AddPersonModal";
import axios from "axios";
import { appParams } from "@/lib/app-params";
import { useAuth } from "@/lib/AuthContext";

const api = axios.create({
  baseURL: appParams.apiUrl,
});

api.interceptors.request.use((config) => {
  const token = appParams.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default function TreeView() {
  const { id } = useParams();
  const { user } = useAuth();

  const [tree, setTree] = useState(null);
  const [members, setMembers] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [relativePerson, setRelativePerson] = useState(null);
  const [editPerson, setEditPerson] = useState(null);
  const [isOwner, setIsOwner] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);

      const [treeRes, membersRes] = await Promise.all([
        api.get(`/trees/${id}`),
        api.get(`/members`, { params: { tree_id: id } }),
      ]);

      setTree(treeRes.data);
      setMembers(membersRes.data);
    } catch (error) {
      console.error("Load tree failed:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && tree) {
      setIsOwner(tree.created_by === user.id || tree.created_by === user.email);
    }
  }, [user, tree]);

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

  // 🔥 SAVE (create/update)
  const handleSave = async (data, existingId, relationType, relPerson) => {
    try {
      if (existingId) {
        const res = await api.patch(`/members/${existingId}`, data);
        setMembers((prev) =>
          prev.map((m) => (m.id === existingId ? res.data : m))
        );
      } else {
        const res = await api.post(`/members`, data);
        const created = res.data;

        // 🔗 связи
        if (relPerson && relationType) {
          if (relationType === "parent") {
            await api.patch(`/members/${relPerson.id}`, {
              parent_ids: [...(relPerson.parent_ids || []), created.id],
            });
          }

          if (relationType === "partner") {
            await Promise.all([
              api.patch(`/members/${created.id}`, { partner_id: relPerson.id }),
              api.patch(`/members/${relPerson.id}`, { partner_id: created.id }),
            ]);
          }
        }

        // проще: перезагрузить
        await loadData();
      }
    } catch (error) {
      console.error("Save failed:", error);
    }
  };

  const togglePublic = async () => {
    try {
      const res = await api.patch(`/trees/${id}`, {
        is_public: !tree.is_public,
      });
      setTree(res.data);
    } catch (error) {
      console.error("Toggle public failed:", error);
    }
  };

  // UI остаётся почти тот же 👇

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        Загрузка...
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        Дерево не найдено
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col">

      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14">
        <div className="flex items-center gap-3">
          <Link to="/dashboard">
            <Button variant="ghost" size="sm">
              <ChevronLeft className="w-4 h-4" />
              Назад
            </Button>
          </Link>

          <span className="font-semibold">{tree.name}</span>
          <span>{members.length} чел.</span>
        </div>

        <div className="flex gap-2">
          {!user && <span>Гость</span>}

          {user && !isOwner && <span>Просмотр</span>}

          {isOwner && (
            <>
              <Button onClick={togglePublic}>
                {tree.is_public ? <EyeOff /> : <Share2 />}
              </Button>

              <Button onClick={() => openAdd(null)}>
                <UserPlus />
              </Button>
            </>
          )}
        </div>
      </header>

      {/* Canvas */}
      <div className="flex-1 flex relative">
        <TreeCanvas
          members={members}
          selectedPerson={selectedPerson}
          onSelectPerson={(p) =>
            setSelectedPerson((prev) =>
              prev?.id === p.id ? null : p
            )
          }
          canEdit={isOwner}
          onAddChild={(parent) => openAdd(parent)}
        />

        <AnimatePresence>
          {selectedPerson && (
            <motion.div
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              exit={{ x: 320 }}
              className="absolute right-0 w-80"
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

      {/* Modal */}
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
