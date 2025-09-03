'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  FileText, 
  ClipboardCheck,
  TrendingUp,
  Search,
  Upload,
  Download,
  RefreshCw
} from "lucide-react"

export default function ComplianceDashboard() {
  const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null)
  const [complianceData] = useState({
    overall: 72,
    compliant: 156,
    nonCompliant: 48,
    partial: 23,
    notApplicable: 89
  })

  // Mock data for demonstration
  const policies = [
    { id: 'AA.1207', name: 'Network Adequacy', category: 'Access & Availability', status: 'partial' },
    { id: 'CMC.3001', name: 'Care Coordination', category: 'Care Management', status: 'compliant' },
    { id: 'GA.2005', name: 'Grievance Process', category: 'Grievance & Appeals', status: 'non_compliant' },
  ]

  const validationResults = [
    { 
      requirement: 'RT APL 23-001 Q1a',
      description: 'Submit data within 30 calendar days',
      status: 'non_compliant',
      gaps: ['Missing: extension clause', 'Missing: 30 day timeframe'],
      confidence: 85
    },
    { 
      requirement: 'RT APL 23-001 Q1b',
      description: 'Submit required ANC exhibits',
      status: 'compliant',
      gaps: [],
      confidence: 92
    },
  ]

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'compliant': return 'bg-green-500'
      case 'non_compliant': return 'bg-red-500'
      case 'partial': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'compliant': return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'non_compliant': return <XCircle className="w-5 h-5 text-red-500" />
      case 'partial': return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default: return <AlertCircle className="w-5 h-5 text-gray-500" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <ClipboardCheck className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Policy Compliance Auditor
                </h1>
                <p className="text-sm text-gray-500">DHCS MCOD Review Tool Validator</p>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                <Upload className="w-4 h-4 mr-2" />
                Import Policies
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Run Audit
              </Button>
              <Button size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export Report
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overall Compliance</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceData.overall}%</div>
              <Progress value={complianceData.overall} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Compliant</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceData.compliant}</div>
              <p className="text-xs text-muted-foreground">Requirements met</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Non-Compliant</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceData.nonCompliant}</div>
              <p className="text-xs text-muted-foreground">Needs attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Partial</CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceData.partial}</div>
              <p className="text-xs text-muted-foreground">In progress</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="policies" className="space-y-4">
          <TabsList>
            <TabsTrigger value="policies">Policies</TabsTrigger>
            <TabsTrigger value="validations">Validation Results</TabsTrigger>
            <TabsTrigger value="gaps">Gap Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="policies" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Policy Documents</CardTitle>
                <CardDescription>
                  Select a policy to view its compliance status against review tools
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2">
                    {policies.map((policy) => (
                      <div
                        key={policy.id}
                        className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 ${
                          selectedPolicy === policy.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : ''
                        }`}
                        onClick={() => setSelectedPolicy(policy.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <FileText className="w-5 h-5 text-gray-400" />
                            <div>
                              <p className="font-medium">{policy.id}</p>
                              <p className="text-sm text-gray-500">{policy.name}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline">{policy.category}</Badge>
                            <Badge className={getStatusColor(policy.status)}>
                              {policy.status.replace('_', ' ')}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="validations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Validation Results</CardTitle>
                <CardDescription>
                  Detailed compliance check results for each requirement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {validationResults.map((result, index) => (
                    <Alert key={index}>
                      <div className="flex items-start space-x-3">
                        {getStatusIcon(result.status)}
                        <div className="flex-1">
                          <AlertTitle className="flex items-center justify-between">
                            <span>{result.requirement}</span>
                            <Badge variant="outline">
                              {result.confidence}% confidence
                            </Badge>
                          </AlertTitle>
                          <AlertDescription className="mt-2">
                            <p>{result.description}</p>
                            {result.gaps.length > 0 && (
                              <div className="mt-2">
                                <p className="font-medium text-red-600">Gaps identified:</p>
                                <ul className="list-disc list-inside text-sm mt-1">
                                  {result.gaps.map((gap, i) => (
                                    <li key={i}>{gap}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </AlertDescription>
                        </div>
                      </div>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="gaps" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Gap Analysis</CardTitle>
                <CardDescription>
                  Identified compliance gaps and recommended actions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>48 Total Gaps Identified</AlertTitle>
                  <AlertDescription className="mt-3 space-y-3">
                    <div className="border-l-4 border-red-500 pl-4">
                      <p className="font-medium">Critical: Network Certification Timeline</p>
                      <p className="text-sm text-gray-600 mt-1">
                        Policy AA.1207 does not specify the 30 calendar day submission requirement
                      </p>
                      <p className="text-sm text-blue-600 mt-2">
                        Recommended: Add "within 30 calendar days" to Section 3.2.1
                      </p>
                    </div>
                    
                    <div className="border-l-4 border-yellow-500 pl-4">
                      <p className="font-medium">Moderate: Extension Provision</p>
                      <p className="text-sm text-gray-600 mt-1">
                        Missing reference to DHCS extension approval process
                      </p>
                      <p className="text-sm text-blue-600 mt-2">
                        Recommended: Add "unless an extension is granted by DHCS" clause
                      </p>
                    </div>
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}