import { executeEmailWorkflow } from '../executors/email';
import {
  createTestContext,
  setupTestDOM,
  createTestEmailDOM,
  MockChromeRuntime,
  waitForPromises
} from './utils/testHelpers';

describe('Email Workflow', () => {
  let mockRuntime: MockChromeRuntime;
  
  beforeEach(() => {
    mockRuntime = new MockChromeRuntime();
    (global as any).chrome = {
      runtime: mockRuntime
    };
    
    // Setup test DOM
    setupTestDOM(createTestEmailDOM());
  });
  
  afterEach(() => {
    jest.clearAllMocks();
    document.body.innerHTML = '';
  });
  
  it('should process unread emails and extract links', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher'
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    // Mock background communication
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'tab.manage') {
        sendResponse({ success: true, data: { tabId: 2 } });
      }
    });
    
    const result = await executeEmailWorkflow(context, selectors);
    
    expect(result.success).toBe(true);
    expect(result.data?.processedCount).toBe(1);
    expect(result.data?.visitedUrls).toContain('https://auktion.hansemerkur.de/test');
  });
  
  it('should handle dry run mode', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher',
      dryRun: true
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    const result = await executeEmailWorkflow(context, selectors);
    
    expect(result.success).toBe(true);
    expect(result.data?.processedCount).toBe(0);
  });
  
  it('should handle no unread emails', async () => {
    // Clear DOM
    setupTestDOM('<div></div>');
    
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher'
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    const result = await executeEmailWorkflow(context, selectors);
    
    expect(result.success).toBe(true);
    expect(result.data?.processedCount).toBe(0);
  });
  
  it('should retry when unread emails are not immediately found', async () => {
    // Start with empty DOM
    setupTestDOM('<div></div>');
    
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher'
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    // Setup DOM after delay
    setTimeout(() => {
      setupTestDOM(createTestEmailDOM());
    }, 100);
    
    const result = await executeEmailWorkflow(context, selectors);
    
    await waitForPromises();
    
    expect(result.success).toBe(true);
    expect(result.data?.processedCount).toBe(1);
  });
  
  it('should mark emails as read', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher'
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    const markAsReadSpy = jest.spyOn(HTMLElement.prototype, 'click');
    
    await executeEmailWorkflow(context, selectors);
    
    expect(markAsReadSpy).toHaveBeenCalled();
  });
  
  it('should handle errors gracefully', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://outlook.office.com/mail/inbox',
      matcherId: 'email-matcher'
    });
    
    const selectors = {
      unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
      emailBody: '#x_body a',
      markAsReadButton: 'span'
    };
    
    // Mock error in background communication
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'tab.manage') {
        sendResponse({ success: false, error: 'Test error' });
      }
    });
    
    const result = await executeEmailWorkflow(context, selectors);
    
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    expect(result.telemetry?.errors.length).toBeGreaterThan(0);
  });
});