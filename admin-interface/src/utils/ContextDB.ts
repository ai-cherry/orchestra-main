import Dexie, { Table } from 'dexie';
import CryptoJS from 'crypto-js';

export interface ContextData {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  metadata: Record<string, any>;
  encryptedContent?: string;
}

const ENCRYPTION_KEY = process.env.VITE_ENCRYPTION_KEY || 'default-dev-key';

function encrypt(text: string): string {
  return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
}

function decrypt(cipher: string): string {
  const bytes = CryptoJS.AES.decrypt(cipher, ENCRYPTION_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}

class ContextDB extends Dexie {
  contexts!: Table<ContextData, string>;

  constructor() {
    super('OrchestraContextDB');
    this.version(1).stores({
      contexts: 'id, type, timestamp'
    });
  }

  async addContext(context: ContextData) {
    const encryptedContent = encrypt(context.content);
    await this.contexts.put({ ...context, encryptedContent });
  }

  async getRecentContexts(limit = 100): Promise<ContextData[]> {
    const results = await this.contexts.orderBy('timestamp').reverse().limit(limit).toArray();
    return results.map(r => ({
      ...r,
      content: r.encryptedContent ? decrypt(r.encryptedContent) : r.content
    }));
  }

  async clearContexts() {
    await this.contexts.clear();
  }
}

export default new ContextDB(); 