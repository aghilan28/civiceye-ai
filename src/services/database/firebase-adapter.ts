import { env } from "@/config/env";
import { civicEyeCollections, type CivicEyeCollectionMap } from "@/services/database/schema";

export type FirebaseAdapterConfig = typeof env.firebase;

export function getFirebaseConfig(): FirebaseAdapterConfig {
  return env.firebase;
}

export function isFirebaseConfigured() {
  return Boolean(env.firebase.apiKey && env.firebase.projectId && env.firebase.appId);
}

export function firebaseCollectionPath<TKey extends keyof CivicEyeCollectionMap>(collection: TKey) {
  return `municipalities/{municipalityId}/${civicEyeCollections[collection]}`;
}

export function firebaseDocumentPath<TKey extends keyof CivicEyeCollectionMap>(collection: TKey, id: string) {
  return `${firebaseCollectionPath(collection)}/${id}`;
}
