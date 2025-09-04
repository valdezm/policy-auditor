'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { CheckCircle2, XCircle, AlertCircle, FileText, ArrowLeft, Eye, Bot, Loader2 } from 'lucide-react';
import Link from 'next/link';

interface PolicyAnalysis {
  policy_id?: string;
  policy_code: string;
  policy_title: string;
  compliance_score: number;
  confidence_level: number;
  is_compliant: boolean;
  has_primary_reference: boolean;
  has_cross_references: boolean;
  missing_elements: string[];
  found_elements: string[];
  explanation: string;
  recommendations: string[];
  contextual_excerpts: Array<{
    text: string;
    context: string;
    relevance_score: number;
    matched_elements: string[];
    surrounding_keywords: string[];
  }>;
}

interface RequirementAnalysis {
  requirement_id: string;
  apl_code: string;
  apl_title: string;
  section_code: string;
  requirement_text: string;
  validation_rule: string;
  analyzer_version: string;
  total_policies_analyzed: number;
  compliant_policies: number;
  high_confidence_analyses: number;
  analyses: PolicyAnalysis[];
}

interface PolicyDetails {
  policy_id: string;
  policy_code: string;
  title: string;
  filename: string;
  extracted_text: string;
  file_size: number;
}

interface AIValidationResult {
  validation_id: string;
  policy_id: string;
  requirement_id: string;
  compliance_rating: string;
  confidence_level: string;
  confidence_score: number;
  reasoning: string;
  specific_findings: string[];
  missing_elements: string[];
  policy_strengths: string[];
  recommendations: string[];
  relevant_policy_excerpts: string[];
  regulatory_interpretation: string;
  risk_assessment: string;
  priority_level: string;
  validation_date: string;
  is_human_reviewed: boolean;
}

export default function RequirementDetailPage() {
  const params = useParams();
  const requirementId = params.id as string;
  const [analysis, setAnalysis] = useState<RequirementAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyDetails | null>(null);
  const [policyModalOpen, setPolicyModalOpen] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [aiValidations, setAiValidations] = useState<{[policyCode: string]: AIValidationResult}>({});
  const [aiValidationLoading, setAiValidationLoading] = useState<{[policyCode: string]: boolean}>({});

  useEffect(() => {
    if (requirementId) {
      fetchAnalysis();
    }
  }, [requirementId]);

  const fetchAnalysis = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/v2/requirements/${requirementId}/enhanced-analysis`);
      if (!response.ok) throw new Error('Failed to fetch analysis');
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  const cleanPolicyTitle = (title: string, code: string) => {
    // If title looks like a filename, just use the policy code
    if (title.includes('.pdf') || title.includes('_CEO') || title.includes('_v20')) {
      return code;
    }
    return title;
  };

  const fetchPolicyDetails = async (policyCode: string) => {
    try {
      // First find the policy ID from the analysis
      const policy = analysis?.analyses.find(a => a.policy_code === policyCode);
      if (!policy) return;
      
      // Use the policy_id from the analysis data, or fallback to policy_code
      const policyIdentifier = policy.policy_id || policy.policy_code;
      
      const response = await fetch(`http://localhost:8001/api/v2/policies/${policyIdentifier}`);
      if (!response.ok) throw new Error('Failed to fetch policy details');
      
      const data = await response.json();
      setSelectedPolicy(data);
      setPolicyModalOpen(true);
    } catch (err) {
      console.error('Error fetching policy details:', err);
    }
  };

  const getComplianceIcon = (isCompliant: boolean, hasPrimaryReference: boolean, hasCrossReferences: boolean) => {
    if (isCompliant) return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    if (hasPrimaryReference || hasCrossReferences) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const getComplianceBadge = (score: number) => {
    if (score >= 0.8) return <Badge className="bg-green-100 text-green-800">Compliant</Badge>;
    if (score >= 0.5) return <Badge className="bg-yellow-100 text-yellow-800">Partial</Badge>;
    if (score > 0) return <Badge className="bg-orange-100 text-orange-800">Minimal</Badge>;
    return <Badge className="bg-red-100 text-red-800">Non-compliant</Badge>;
  };

  const getAIComplianceBadge = (rating: string) => {
    switch (rating) {
      case 'fully_compliant':
        return <Badge className="bg-green-100 text-green-800">✓ Fully Compliant</Badge>;
      case 'partially_compliant':
        return <Badge className="bg-yellow-100 text-yellow-800">⚠ Partially Compliant</Badge>;
      case 'non_compliant':
        return <Badge className="bg-red-100 text-red-800">✗ Non-compliant</Badge>;
      case 'unclear':
        return <Badge className="bg-gray-100 text-gray-800">? Unclear</Badge>;
      case 'not_applicable':
        return <Badge className="bg-blue-100 text-blue-800">N/A Not Applicable</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'high':
        return <Badge variant="destructive">High Priority</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800">Medium Priority</Badge>;
      case 'low':
        return <Badge className="bg-green-100 text-green-800">Low Priority</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{priority}</Badge>;
    }
  };

  const requestAIValidation = async (policyCode: string) => {
    // Find the policy analysis to get the policy details
    const policyAnalysis = analysis?.analyses.find(a => a.policy_code === policyCode);
    if (!policyAnalysis || !analysis) return;

    setAiValidationLoading(prev => ({ ...prev, [policyCode]: true }));

    try {
      // Use the policy_id from the analysis, or fallback to policy_code
      const policyIdentifier = policyAnalysis.policy_id || policyAnalysis.policy_code;

      const response = await fetch('http://localhost:8001/api/v2/ai-validation/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          policy_id: policyIdentifier,
          requirement_id: requirementId,
          requirement_text: analysis.requirement_text,
          regulation_reference: `${analysis.apl_code} ${analysis.section_code}`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to request AI validation');
      }

      const validationResult: AIValidationResult = await response.json();
      setAiValidations(prev => ({
        ...prev,
        [policyCode]: validationResult
      }));

    } catch (error) {
      console.error('Error requesting AI validation:', error);
      // You could add error state handling here
    } finally {
      setAiValidationLoading(prev => ({ ...prev, [policyCode]: false }));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading analysis...</div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen p-8">
        <Alert variant="destructive">
          <AlertDescription>{error || 'No analysis available'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link href="/requirements" className="flex items-center text-blue-600 hover:text-blue-800 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Requirements
          </Link>
          <h1 className="text-3xl font-bold">{analysis.apl_code} - {analysis.section_code}</h1>
          <h2 className="text-xl text-gray-700 mt-2 mb-4">{analysis.apl_title}</h2>
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
            <p className="text-gray-800">{analysis.requirement_text}</p>
          </div>
          <p className="text-gray-600">
            Analyzed {analysis.total_policies_analyzed} policies • 
            {analysis.compliant_policies} compliant • 
            {analysis.high_confidence_analyses} high confidence
            {analysis.analyzer_version && (
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {analysis.analyzer_version}
              </span>
            )}
          </p>
        </div>

        {/* Summary Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Compliance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div 
                className={`text-center cursor-pointer hover:bg-green-50 p-2 rounded transition-colors ${filterType === 'compliant' ? 'bg-green-100 ring-2 ring-green-500' : ''}`}
                onClick={() => setFilterType(filterType === 'compliant' ? 'all' : 'compliant')}
              >
                <div className="text-2xl font-bold text-green-600">
                  {analysis.analyses.filter(a => a.is_compliant).length}
                </div>
                <p className="text-sm text-gray-600">Fully Compliant</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-yellow-50 p-2 rounded transition-colors ${filterType === 'reference' ? 'bg-yellow-100 ring-2 ring-yellow-500' : ''}`}
                onClick={() => setFilterType(filterType === 'reference' ? 'all' : 'reference')}
              >
                <div className="text-2xl font-bold text-yellow-600">
                  {analysis.analyses.filter(a => !a.is_compliant && (a.has_primary_reference || a.has_cross_references)).length}
                </div>
                <p className="text-sm text-gray-600">References Only</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-orange-50 p-2 rounded transition-colors ${filterType === 'partial' ? 'bg-orange-100 ring-2 ring-orange-500' : ''}`}
                onClick={() => setFilterType(filterType === 'partial' ? 'all' : 'partial')}
              >
                <div className="text-2xl font-bold text-orange-600">
                  {analysis.analyses.filter(a => !a.is_compliant && !a.has_primary_reference && !a.has_cross_references && a.compliance_score > 0).length}
                </div>
                <p className="text-sm text-gray-600">Partial Coverage</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-red-50 p-2 rounded transition-colors ${filterType === 'none' ? 'bg-red-100 ring-2 ring-red-500' : ''}`}
                onClick={() => setFilterType(filterType === 'none' ? 'all' : 'none')}
              >
                <div className="text-2xl font-bold text-red-600">
                  {analysis.analyses.filter(a => a.compliance_score === 0).length}
                </div>
                <p className="text-sm text-gray-600">No Coverage</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Policy Analyses */}
        <div className="space-y-6">
          {analysis.analyses
            .filter((policyAnalysis) => {
              if (filterType === 'all') return true;
              if (filterType === 'compliant') return policyAnalysis.is_compliant;
              if (filterType === 'reference') return !policyAnalysis.is_compliant && (policyAnalysis.has_primary_reference || policyAnalysis.has_cross_references);
              if (filterType === 'partial') return !policyAnalysis.is_compliant && !policyAnalysis.has_primary_reference && !policyAnalysis.has_cross_references && policyAnalysis.compliance_score > 0;
              if (filterType === 'none') return policyAnalysis.compliance_score === 0;
              return true;
            })
            .map((policyAnalysis) => (
            <Card key={policyAnalysis.policy_code} 
                  className={policyAnalysis.is_compliant ? 'border-green-200' : 
                            (policyAnalysis.has_primary_reference || policyAnalysis.has_cross_references) ? 'border-yellow-200' : 
                            'border-red-200'}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getComplianceIcon(policyAnalysis.is_compliant, policyAnalysis.has_primary_reference, policyAnalysis.has_cross_references)}
                    <div>
                      <CardTitle className="text-xl">
                        <Button
                          variant="link"
                          className="p-0 h-auto font-bold text-xl text-left"
                          onClick={() => fetchPolicyDetails(policyAnalysis.policy_code)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          {cleanPolicyTitle(policyAnalysis.policy_title, policyAnalysis.policy_code)}
                        </Button>
                      </CardTitle>
                      <CardDescription>
                        Compliance Score: {(policyAnalysis.compliance_score * 100).toFixed(0)}% • 
                        Confidence: {(policyAnalysis.confidence_level * 100).toFixed(0)}%
                      </CardDescription>
                    </div>
                  </div>
                  {getComplianceBadge(policyAnalysis.compliance_score)}
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="explanation" className="w-full">
                  <TabsList>
                    <TabsTrigger value="explanation">Explanation</TabsTrigger>
                    <TabsTrigger value="elements">Elements</TabsTrigger>
                    <TabsTrigger value="excerpts">Excerpts</TabsTrigger>
                    <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                    <TabsTrigger value="ai-validation" className="flex items-center gap-2">
                      <Bot className="w-4 h-4" />
                      AI Validation
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="explanation" className="mt-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <pre className="whitespace-pre-wrap text-sm">{policyAnalysis.explanation}</pre>
                    </div>
                  </TabsContent>

                  <TabsContent value="elements" className="mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2 flex items-center">
                          <CheckCircle2 className="w-4 h-4 text-green-600 mr-2" />
                          Found Elements ({policyAnalysis.found_elements.length})
                        </h4>
                        <ul className="space-y-1">
                          {policyAnalysis.found_elements.map((element, idx) => (
                            <li key={idx} className="text-sm bg-green-50 p-2 rounded">
                              ✓ {element}
                            </li>
                          ))}
                          {policyAnalysis.found_elements.length === 0 && (
                            <li className="text-sm text-gray-500 italic">None found</li>
                          )}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2 flex items-center">
                          <XCircle className="w-4 h-4 text-red-600 mr-2" />
                          Missing Elements ({policyAnalysis.missing_elements.length})
                        </h4>
                        <ul className="space-y-1">
                          {policyAnalysis.missing_elements.map((element, idx) => (
                            <li key={idx} className="text-sm bg-red-50 p-2 rounded">
                              ✗ {element}
                            </li>
                          ))}
                          {policyAnalysis.missing_elements.length === 0 && (
                            <li className="text-sm text-gray-500 italic">All requirements met</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="excerpts" className="mt-4">
                    {policyAnalysis.contextual_excerpts && policyAnalysis.contextual_excerpts.length > 0 ? (
                      <div className="space-y-3">
                        {policyAnalysis.contextual_excerpts.map((excerpt, idx) => (
                          <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <p className="text-sm font-mono">Match: &quot;{excerpt.text}&quot;</p>
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                Relevance: {(excerpt.relevance_score * 100).toFixed(0)}%
                              </span>
                            </div>
                            {excerpt.matched_elements && excerpt.matched_elements.length > 0 && (
                              <div className="mb-2">
                                <p className="text-xs text-gray-600">Matched elements:</p>
                                <div className="flex flex-wrap gap-1">
                                  {excerpt.matched_elements.map((element, i) => (
                                    <span key={i} className="text-xs bg-green-100 text-green-800 px-1 py-0.5 rounded">
                                      {element}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            <div className="text-sm text-gray-700 border-l-4 border-blue-400 pl-4">
                              {excerpt.context.split('**').map((part, i) => 
                                i % 2 === 0 ? part : <mark key={i} className="bg-yellow-200">{part}</mark>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">No relevant excerpts found</p>
                    )}
                  </TabsContent>

                  <TabsContent value="recommendations" className="mt-4">
                    {policyAnalysis.recommendations.length > 0 ? (
                      <ul className="space-y-2">
                        {policyAnalysis.recommendations.map((rec, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-blue-600 mr-2">→</span>
                            <span className="text-sm">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-green-600">
                        ✓ No recommendations - policy appears complete for this requirement
                      </p>
                    )}
                  </TabsContent>

                  <TabsContent value="ai-validation" className="mt-4">
                    {aiValidations[policyAnalysis.policy_code] ? (
                      // Show AI validation result
                      <div className="space-y-4">
                        {/* Header with compliance rating and confidence */}
                        <div className="flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
                          <div className="flex items-center gap-3">
                            <Bot className="w-6 h-6 text-blue-600" />
                            <div>
                              <h3 className="font-semibold">AI Analysis Complete</h3>
                              <p className="text-sm text-gray-600">
                                Confidence: {Math.round(aiValidations[policyAnalysis.policy_code].confidence_score)}% • 
                                {aiValidations[policyAnalysis.policy_code].confidence_level}
                              </p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {getAIComplianceBadge(aiValidations[policyAnalysis.policy_code].compliance_rating)}
                            {getPriorityBadge(aiValidations[policyAnalysis.policy_code].priority_level)}
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div className="bg-white p-4 rounded-lg border">
                          <h4 className="font-medium mb-2 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-blue-600" />
                            AI Reasoning
                          </h4>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {aiValidations[policyAnalysis.policy_code].reasoning}
                          </p>
                        </div>

                        {/* Findings Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Strengths */}
                          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-green-800">
                              <CheckCircle2 className="w-4 h-4" />
                              Policy Strengths ({aiValidations[policyAnalysis.policy_code].policy_strengths.length})
                            </h4>
                            <ul className="space-y-1">
                              {aiValidations[policyAnalysis.policy_code].policy_strengths.map((strength, idx) => (
                                <li key={idx} className="text-sm text-green-700">
                                  ✓ {strength}
                                </li>
                              ))}
                              {aiValidations[policyAnalysis.policy_code].policy_strengths.length === 0 && (
                                <li className="text-sm text-gray-500 italic">None identified</li>
                              )}
                            </ul>
                          </div>

                          {/* Missing Elements */}
                          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-red-800">
                              <XCircle className="w-4 h-4" />
                              Missing Elements ({aiValidations[policyAnalysis.policy_code].missing_elements.length})
                            </h4>
                            <ul className="space-y-1">
                              {aiValidations[policyAnalysis.policy_code].missing_elements.map((element, idx) => (
                                <li key={idx} className="text-sm text-red-700">
                                  ✗ {element}
                                </li>
                              ))}
                              {aiValidations[policyAnalysis.policy_code].missing_elements.length === 0 && (
                                <li className="text-sm text-gray-500 italic">All requirements met</li>
                              )}
                            </ul>
                          </div>
                        </div>

                        {/* AI Recommendations */}
                        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                          <h4 className="font-medium mb-2 flex items-center gap-2 text-yellow-800">
                            <AlertCircle className="w-4 h-4" />
                            AI Recommendations ({aiValidations[policyAnalysis.policy_code].recommendations.length})
                          </h4>
                          <ul className="space-y-1">
                            {aiValidations[policyAnalysis.policy_code].recommendations.map((rec, idx) => (
                              <li key={idx} className="text-sm text-yellow-700">
                                → {rec}
                              </li>
                            ))}
                            {aiValidations[policyAnalysis.policy_code].recommendations.length === 0 && (
                              <li className="text-sm text-gray-500 italic">No recommendations</li>
                            )}
                          </ul>
                        </div>

                        {/* Risk Assessment */}
                        {aiValidations[policyAnalysis.policy_code].risk_assessment && (
                          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-orange-800">
                              <AlertCircle className="w-4 h-4" />
                              Risk Assessment
                            </h4>
                            <p className="text-sm text-orange-700">
                              {aiValidations[policyAnalysis.policy_code].risk_assessment}
                            </p>
                          </div>
                        )}

                        {/* Regulatory Interpretation */}
                        {aiValidations[policyAnalysis.policy_code].regulatory_interpretation && (
                          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-blue-800">
                              <FileText className="w-4 h-4" />
                              Regulatory Interpretation
                            </h4>
                            <p className="text-sm text-blue-700">
                              {aiValidations[policyAnalysis.policy_code].regulatory_interpretation}
                            </p>
                          </div>
                        )}

                        {/* Relevant Excerpts */}
                        {aiValidations[policyAnalysis.policy_code].relevant_policy_excerpts.length > 0 && (
                          <div className="bg-gray-50 p-4 rounded-lg border">
                            <h4 className="font-medium mb-2 flex items-center gap-2">
                              <Eye className="w-4 h-4" />
                              Relevant Policy Excerpts
                            </h4>
                            <div className="space-y-2">
                              {aiValidations[policyAnalysis.policy_code].relevant_policy_excerpts.map((excerpt, idx) => (
                                <div key={idx} className="bg-white p-3 rounded border-l-4 border-blue-400">
                                  <p className="text-sm italic">"{excerpt}"</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Footer info */}
                        <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded border-t">
                          Analysis completed: {new Date(aiValidations[policyAnalysis.policy_code].validation_date).toLocaleString()} • 
                          {aiValidations[policyAnalysis.policy_code].is_human_reviewed ? ' Human reviewed' : ' Pending human review'}
                        </div>
                      </div>
                    ) : (
                      // Show request AI validation button
                      <div className="text-center py-8">
                        {aiValidationLoading[policyAnalysis.policy_code] ? (
                          <div className="flex flex-col items-center gap-4">
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                              <span className="text-sm text-gray-600">AI is analyzing policy compliance...</span>
                            </div>
                            <p className="text-xs text-gray-500">This may take 10-30 seconds</p>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center gap-4">
                            <div className="flex items-center gap-2 text-gray-600">
                              <Bot className="w-8 h-8" />
                              <div>
                                <h3 className="font-medium">AI Validation Available</h3>
                                <p className="text-sm text-gray-500">Get detailed AI-powered compliance analysis</p>
                              </div>
                            </div>
                            <Button 
                              onClick={() => requestAIValidation(policyAnalysis.policy_code)}
                              className="flex items-center gap-2"
                              size="sm"
                            >
                              <Bot className="w-4 h-4" />
                              Request AI Analysis
                            </Button>
                            <p className="text-xs text-gray-500 max-w-md">
                              AI analysis uses GPT-4 to provide detailed compliance assessment, 
                              risk evaluation, and specific recommendations for improvement.
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Policy Modal */}
        <Dialog open={policyModalOpen} onOpenChange={setPolicyModalOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Policy: {selectedPolicy?.title || selectedPolicy?.policy_code}
              </DialogTitle>
              <DialogDescription>
                Full policy text ({selectedPolicy?.file_size ? Math.round(selectedPolicy.file_size / 1000) : 0}KB)
              </DialogDescription>
            </DialogHeader>
            
            <div className="mt-4">
              {selectedPolicy ? (
                <div className="bg-gray-50 p-4 rounded-lg border">
                  <div className="mb-4 text-sm text-gray-600">
                    <strong>File:</strong> {selectedPolicy.filename}
                  </div>
                  <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                    {selectedPolicy.extracted_text || 'No text content available.'}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading policy content...</p>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}