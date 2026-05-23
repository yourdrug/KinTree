/**
 * api/persons.js
 */

import { http } from "./http";
import { ENDPOINTS as EP } from "./endpoints";

export const personsApi = {
  list:   (params)   => http.get(EP.persons.list(),      { params }).then((r) => r.data),
  get:    (id)       => http.get(EP.persons.detail(id)).then((r) => r.data),
  create: (data)     => http.post(EP.persons.create(), data).then((r) => r.data),
  patch:  (id, data) => http.patch(EP.persons.patch(id), data).then((r) => r.data),
  delete: (id)       => http.delete(EP.persons.delete(id)).then((r) => r.data),
};
