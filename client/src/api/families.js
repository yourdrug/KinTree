/**
 * api/families.js
 */

import { http } from "./http";
import { ENDPOINTS as EP } from "./endpoints";

export const familiesApi = {
  list:   (params) => http.get(EP.families.list(),    { params }).then((r) => r.data),
  get:    (id)     => http.get(EP.families.detail(id)).then((r) => r.data),
  create: (data)   => http.post(EP.families.create(), data).then((r) => r.data),
  patch:  (id, d)  => http.patch(EP.families.patch(id), d).then((r) => r.data),
  delete: (id)     => http.delete(EP.families.delete(id)).then((r) => r.data),
  setPublic:   (id, is_public) => http.patch(EP.families.patch(id), { is_public }).then((r) => r.data),
};
