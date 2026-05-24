import { civicEyeCollections, type CivicEyeCollectionMap } from "@/services/database/schema";

export type MongoDocument<T> = T & {
  _id?: string;
  createdAt?: string;
  updatedAt?: string;
};

export function buildMongoCollectionPath<TKey extends keyof CivicEyeCollectionMap>(collection: TKey) {
  return `/collections/${civicEyeCollections[collection]}`;
}

export function buildMongoMunicipalityScopedQuery<TKey extends keyof CivicEyeCollectionMap>(collection: TKey, municipalityId: string) {
  return {
    collection: civicEyeCollections[collection],
    filter: { municipalityId }
  };
}
