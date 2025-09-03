'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface CoverageData {
  overall_coverage: number;
  total_requirements: number;
  covered: number;
  partial: number;
  uncovered: number;
  by_rt_apl: Array<{
    apl_code: string;
    total: number;
    covered: number;
    partial: number;
    uncovered: number;
    requirements: Array<{
      id: string;
      text: string;
      status: string;
      policies: string[];
      confidence: number;
    }>;
  }>;
}

export default function CoverageDashboard() {
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAPL, setExpandedAPL] = useState<string | null>(null);

  useEffect(() => {
    fetchCoverageData();
  }, []);

  const fetchCoverageData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/coverage/summary');
      if (!response.ok) throw new Error('Failed to fetch coverage data');
      const data = await response.json();
      setCoverage(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load coverage data');
    } finally {
      setLoading(false);
    }
  };


  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'covered': return <Badge className="bg-green-100 text-green-800">Covered</Badge>;
      case 'partial': return <Badge className="bg-yellow-100 text-yellow-800">Partial</Badge>;
      case 'uncovered': return <Badge className="bg-red-100 text-red-800">Uncovered</Badge>;
      default: return <Badge>Unknown</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading coverage data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!coverage) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Policy Corpus Coverage Analysis</h1>
        
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Overall Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{coverage.overall_coverage.toFixed(1)}%</div>
              <Progress value={coverage.overall_coverage} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Covered</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{coverage.covered}</div>
              <p className="text-xs text-gray-500">Requirements</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Partial</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{coverage.partial}</div>
              <p className="text-xs text-gray-500">Requirements</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Uncovered</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{coverage.uncovered}</div>
              <p className="text-xs text-gray-500">Requirements</p>
            </CardContent>
          </Card>
        </div>

        {/* RT APL Details */}
        <Card>
          <CardHeader>
            <CardTitle>RT APL Coverage Details</CardTitle>
            <CardDescription>
              Click on an APL to see requirement details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>APL Code</TableHead>
                  <TableHead>Total Requirements</TableHead>
                  <TableHead>Covered</TableHead>
                  <TableHead>Partial</TableHead>
                  <TableHead>Uncovered</TableHead>
                  <TableHead>Coverage</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {coverage.by_rt_apl.map((apl) => (
                  <>
                    <TableRow 
                      key={apl.apl_code}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => setExpandedAPL(expandedAPL === apl.apl_code ? null : apl.apl_code)}
                    >
                      <TableCell className="font-medium">{apl.apl_code}</TableCell>
                      <TableCell>{apl.total}</TableCell>
                      <TableCell className="text-green-600">{apl.covered}</TableCell>
                      <TableCell className="text-yellow-600">{apl.partial}</TableCell>
                      <TableCell className="text-red-600">{apl.uncovered}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress 
                            value={(apl.covered + apl.partial * 0.5) / apl.total * 100} 
                            className="w-20"
                          />
                          <span className="text-sm text-gray-500">
                            {((apl.covered + apl.partial * 0.5) / apl.total * 100).toFixed(0)}%
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                    
                    {expandedAPL === apl.apl_code && (
                      <TableRow>
                        <TableCell colSpan={6} className="bg-gray-50 p-4">
                          <div className="space-y-3">
                            <h4 className="font-semibold mb-2">Requirements:</h4>
                            {apl.requirements.map((req, idx) => (
                              <div key={`${apl.apl_code}-${idx}`} className="border-l-4 pl-4 py-2"
                                   style={{borderColor: req.status === 'covered' ? '#10b981' : 
                                          req.status === 'partial' ? '#f59e0b' : '#ef4444'}}>
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="font-mono text-sm">{req.id}</span>
                                      {getStatusBadge(req.status)}
                                      <span className="text-xs text-gray-500">
                                        Confidence: {(req.confidence * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    <p className="text-sm text-gray-700 mb-2">{req.text}</p>
                                    {req.policies.length > 0 && (
                                      <div className="flex flex-wrap gap-1">
                                        <span className="text-xs text-gray-500">Policies:</span>
                                        {req.policies.map((policy) => (
                                          <Badge key={policy} variant="outline" className="text-xs">
                                            {policy}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
