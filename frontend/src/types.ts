export interface AnalysisProgress {
    status: 'processing' | 'completed' | 'error';
    current_ticket?: number;
    total_tickets?: number;
    progress_percentage?: number;
    error?: string;
    results?: AnalysisResults;
  }
  
  export interface AnalysisResults {
    metadata: {
      analyzed_at: string;
      file_path: string;
      llm_provider: string;
      total_raw_rows: number;
      unique_tickets: number;
    };
    ticket_summaries: TicketSummary[];
    diagnostics_analysis: DiagnosticsAnalysis;
    author_outreach_list: AuthorOutreach[];
  }
  
  export interface TicketSummary {
    ticket_id: string;
    ent_id: string;
    subject: string;
    issue_summary: string;
    resolution_summary: string;
    derived_category: string;
    resolution_type: string;
    original_category: string;
    original_root_cause: string;
    comment_count: number;
    conversation_metadata?: {
      total_exchanges: number;
      customer_messages: number;
      agent_messages: number;
    };
  }
  
  export interface DiagnosticsAnalysis {
    summary: {
      total_tickets: number;
      diagnostics_compatible_count: number;
      diagnostics_compatible_percentage: string;
      complex_issues_count: number;
    };
    category_distribution: Record<string, number>;
    resolution_type_distribution: Record<string, number>;
    diagnostics_compatible_tickets: DiagnosticsCompatibleTicket[];
    complex_issues: ComplexIssue[];
    recommendations: Recommendation[];
  }
  
  export interface DiagnosticsCompatibleTicket {
    ticket_id: string;
    is_diagnostics_compatible: boolean;
    compatibility_score: number;
    checks: {
      element_detection: boolean;
      visibility_rules: boolean;
      simple_css_fix: boolean;
      configuration_issue: boolean;
      requires_code_change: boolean;
      requires_human_analysis: boolean;
    };
    recommendation: string;
    author_email: string;
  }
  
  export interface ComplexIssue {
    ticket_id: string;
    issue: string;
    comment_count: number;
  }
  
  export interface Recommendation {
    type: string;
    recommendation: string;
    reason: string;
  }
  
  export interface AuthorOutreach {
    ticket_id: string;
    author_email: string;
    issue_summary: string;
    resolution_summary: string;
    derived_category: string;
    resolution_type: string;
    could_use_diagnostics: boolean;
  }